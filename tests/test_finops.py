"""SubagentStop FinOps hook: transcript parsing and the opt-in logging behaviour."""
import json
import os
import subprocess
import sys
import unittest
from datetime import datetime

from ._common import IsolatedTestCase, SCRIPTS, finops_hook, subprocess_env


def usage(inp=0, out=0, cache_read=0, cache_write=0):
    return {"input_tokens": inp, "output_tokens": out,
            "cache_read_input_tokens": cache_read, "cache_creation_input_tokens": cache_write}


def assistant(msg_id, model, **usage_kwargs):
    return json.dumps({"type": "assistant", "uuid": f"uuid-{msg_id}",
                       "message": {"id": msg_id, "role": "assistant", "model": model, "usage": usage(**usage_kwargs)}})


# Two lines share one API response (m1: streamed copies grow), a second response, and noise.
TRANSCRIPT = [
    assistant("m1", "model-haiku", inp=10, out=5, cache_read=100, cache_write=0),
    "this is not json",
    json.dumps({"type": "user", "message": {"role": "user", "content": "hello"}}),
    assistant("m1", "model-haiku", inp=10, out=50, cache_read=100, cache_write=7),
    "",
    json.dumps({"type": "summary", "summary": "no message here"}),
    json.dumps([1, 2, 3]),
    "null",
    json.dumps({"message": {"id": "m9", "usage": "not-a-dict"}}),
    assistant("m2", "model-sonnet", inp=3, out=4, cache_read=0, cache_write=2),
]


class UsageFromTranscriptTests(IsolatedTestCase):
    def write(self, lines):
        path = self.tmp / "transcript.jsonl"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    def test_counts_each_message_once_taking_the_max_per_field(self):
        totals, models, responses = finops_hook.usage_from_transcript(self.write(TRANSCRIPT))
        self.assertEqual(totals, {"input_tokens": 13, "output_tokens": 54,
                                  "cache_read_tokens": 100, "cache_write_tokens": 9})
        self.assertEqual(models, ["model-haiku", "model-sonnet"])
        self.assertEqual(responses, 2)
        noise = self.write(["{", json.dumps({"type": "user", "message": {"content": "x"}}), "[]", "7"])
        self.assertEqual(finops_hook.usage_from_transcript(noise),
                         ({"input_tokens": 0, "output_tokens": 0, "cache_read_tokens": 0, "cache_write_tokens": 0}, [], 0))

    def test_messages_without_ids_fall_back_to_uuid_then_line_number(self):
        def line(uuid, tokens):
            msg = {"usage": usage(inp=tokens)}
            entry = {"message": msg}
            if uuid:
                entry["uuid"] = uuid
            return json.dumps(entry)
        path = self.write([line("u1", 5), line("u1", 8), line("u2", 1), line(None, 2), line(None, 2)])
        totals, _, responses = finops_hook.usage_from_transcript(path)
        self.assertEqual(responses, 4)             # u1 (merged), u2, two uuid-less lines
        self.assertEqual(totals["input_tokens"], 8 + 1 + 2 + 2)

    def test_non_integer_counters_are_ignored(self):
        bad = json.dumps({"message": {"id": "z", "usage": {"input_tokens": "10", "output_tokens": 2.5,
                                                          "cache_read_input_tokens": None, "cache_creation_input_tokens": 4}}})
        totals, _, responses = finops_hook.usage_from_transcript(self.write([bad]))
        self.assertEqual((totals["input_tokens"], totals["output_tokens"], totals["cache_write_tokens"], responses),
                         (0, 0, 4, 1))


class FinopsMainTests(IsolatedTestCase):
    def setUp(self):
        super().setUp()
        self.transcript = self.tmp / "agent-transcript.jsonl"
        self.transcript.write_text("\n".join(TRANSCRIPT) + "\n", encoding="utf-8")
        self.project = self.tmp / "project"
        self.project.mkdir()
        os.environ["CLAUDE_PROJECT_DIR"] = str(self.project)
        self.log = self.project / ".oeo" / "finops.jsonl"

    def payload(self, **over):
        base = {"session_id": "s1", "agent_type": "oeo:junior-developer", "agent_id": "a-1",
                "agent_transcript_path": str(self.transcript)}
        base.update(over)
        return json.dumps(base)

    def test_writes_one_record_when_the_project_has_an_oeo_directory(self):
        (self.project / ".oeo").mkdir()
        self.assertEqual(self.run_hook(finops_hook, self.payload()), (0, ""))
        records = [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len(records), 1)
        rec = records[0]
        self.assertEqual((rec["session_id"], rec["agent_type"], rec["agent_id"]), ("s1", "oeo:junior-developer", "a-1"))
        self.assertEqual((rec["input_tokens"], rec["output_tokens"], rec["cache_read_tokens"], rec["cache_write_tokens"]),
                         (13, 54, 100, 9))
        self.assertEqual((rec["models"], rec["api_responses"]), (["model-haiku", "model-sonnet"], 2))
        datetime.fromisoformat(rec["ts"])  # valid ISO timestamp
        self.run_hook(finops_hook, self.payload(agent_id="a-2"))
        self.assertEqual(len(self.log.read_text(encoding="utf-8").splitlines()), 2)  # appends
        del os.environ["CLAUDE_PROJECT_DIR"]  # without it the payload's cwd decides where to log
        self.log.unlink()
        self.run_hook(finops_hook, self.payload(cwd=str(self.project)))
        self.assertTrue(self.log.exists())

    def test_writes_nothing_without_an_oeo_directory(self):
        self.assertEqual(self.run_hook(finops_hook, self.payload()), (0, ""))
        self.assertFalse((self.project / ".oeo").exists())
        self.assertEqual(list(self.project.iterdir()), [])

    def test_oeo_finops_off_disables_logging(self):
        (self.project / ".oeo").mkdir()
        for value in ("off", "OFF", "0", "false"):
            with self.subTest(value=value):
                os.environ["OEO_FINOPS"] = value
                self.assertEqual(self.run_hook(finops_hook, self.payload()), (0, ""))
                self.assertFalse(self.log.exists())

    def test_never_raises_on_bad_input(self):
        (self.project / ".oeo").mkdir()
        binary = self.tmp / "binary.jsonl"
        binary.write_bytes(b"\xff\xfe\x00 not utf-8 \x80\n")
        directory = self.tmp / "a-directory"
        directory.mkdir()
        cases = ["", "not json", "{", "null", "[]", "5", '"text"', "{}",
                 self.payload(agent_transcript_path=None),
                 self.payload(agent_transcript_path=str(self.tmp / "missing.jsonl")),
                 self.payload(agent_transcript_path=str(directory)),
                 self.payload(agent_transcript_path=str(binary)),
                 self.payload(agent_transcript_path=12345)]
        for stdin in cases:
            with self.subTest(stdin=stdin[:60]):
                self.assertEqual(self.run_hook(finops_hook, stdin), (0, ""))
        self.assertFalse(self.log.exists())

    def test_script_entry_point_end_to_end(self):
        (self.project / ".oeo").mkdir()
        proc = subprocess.run([sys.executable, "-I", "-B", str(SCRIPTS / "finops_hook.py")], input=self.payload(),
                              text=True, capture_output=True, timeout=30,
                              env=subprocess_env(CLAUDE_PROJECT_DIR=str(self.project)))
        self.assertEqual((proc.returncode, proc.stdout, proc.stderr), (0, "", ""))
        self.assertEqual(json.loads(self.log.read_text(encoding="utf-8"))["input_tokens"], 13)


if __name__ == "__main__":
    unittest.main()
