import io
import zipfile

from app.services.zip_processor import ZipProcessor


def _build_valid_zip() -> bytes:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("docker-compose.yml", "services: {}\n")
        archive.writestr(
            "challenge.yaml",
            "\n".join(
                [
                    'name: "Demo Challenge"',
                    'description: "A demo challenge"',
                    'flag: "CTF{demo_flag}"',
                    'difficulty: "simple"',
                    "verify:",
                    '  script: "verify.py"',
                    '  language: "python"',
                    "  timeout: 20",
                    "deployment:",
                    '  remote_dir: "/home/student/challenge"',
                    "services:",
                    '  - name: "web"',
                    '    protocol: "http"',
                    '    host: "127.0.0.1"',
                    "    port: 8080",
                    '    path: "/"',
                    "    expected_status: 200",
                    "validation_steps:",
                    '  - type: "container_running"',
                    '  - type: "service_check"',
                    '    service: "web"',
                    '  - type: "verify_script"',
                ]
            ),
        )
        archive.writestr("verify.py", "print('CTF{demo_flag}')\n")
        archive.writestr("writeup.md", "# Writeup\n")
    return stream.getvalue()


def test_zip_processor_accepts_valid_archive(tmp_path):
    upload = tmp_path / "uploads"
    extract = tmp_path / "extract"
    processor = ZipProcessor(str(upload), str(extract))
    result = processor.save_and_extract("submission.zip", _build_valid_zip())
    assert result.challenge.name == "Demo Challenge"
    assert result.challenge.verify.script == "verify.py"
