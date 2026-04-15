from app.services.ssh_service import RemoteCommandResult


def test_remote_command_result_struct():
    result = RemoteCommandResult(command="echo test", exit_code=0, stdout="test", stderr="")
    assert result.exit_code == 0
    assert "test" in result.stdout
