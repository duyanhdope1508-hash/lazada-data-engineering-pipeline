import os
from subprocess import Popen, PIPE

def run_command(command):
    process = Popen(command, stdout=PIPE, stderr=PIPE, shell=True)
    output, error = process.communicate()
    return output, error

def init_superset():
    commands = [
        "docker-compose exec -T superset superset db upgrade",
        "docker-compose exec -T superset superset init",
        "docker-compose exec -T superset superset fab create-admin "
        "--username admin "
        "--firstname Superset "
        "--lastname Admin "
        "--email admin@superset.com "
        "--password admin"
    ]

    for cmd in commands:
        print(f"Running: {cmd}")
        output, error = run_command(cmd)
        print(f"Output: {output.decode()}")
        if error:
            print(f"Error: {error.decode()}")

if __name__ == "__main__":
    init_superset()