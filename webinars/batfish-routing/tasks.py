"""Tasks for use with Invoke."""
import os
import sys
from distutils.util import strtobool

from invoke import Collection
from invoke import task as invoke_task
from invoke.exceptions import Exit

try:
    import toml
except ImportError:
    sys.exit("Please make sure to `pip install toml` or enable the Poetry shell and run `poetry install`.")


def is_truthy(arg):
    """Convert "truthy" strings into Booleans.
    Args:
        arg (str): Truthy string (True values are y, yes, t, true, on and 1; false values are n, no,
        f, false, off and 0. Raises ValueError if val is anything else.
    Examples:
        >>> is_truthy('yes')
        True
    """
    if isinstance(arg, bool):
        return arg
    return bool(strtobool(arg))


namespace = Collection("batfish_routing")
namespace.configure(
    {
        "batfish_routing": {
            "project_name": "batfish_routing",
            "python_ver": "3.9",
            "local": False,
            "compose_dir": os.path.join(os.path.dirname(__file__), "development/"),
            "compose_files": [
                "docker-compose.yml",
            ]
        }
    }
)


def task(function=None, *args, **kwargs):
    """Task decorator to override the default Invoke task decorator."""

    def task_wrapper(function=None):
        """Wrapper around invoke.task to add the task to the namespace as well."""
        if args or kwargs:
            task_func = invoke_task(*args, **kwargs)(function)
        else:
            task_func = invoke_task(function)
        namespace.add_task(task_func)
        return task_func

    if function:
        # The decorator was called with no arguments
        return task_wrapper(function)
    # The decorator was called with arguments
    return task_wrapper

PYPROJECT_CONFIG = toml.load("pyproject.toml")
TOOL_CONFIG = PYPROJECT_CONFIG["tool"]["poetry"]

# Can be set to a separate Python version to be used for launching or building image
PYTHON_VER = os.getenv("PYTHON_VER", "3.9")
# Name of the docker image/image
IMAGE_NAME = os.getenv("IMAGE_NAME", TOOL_CONFIG["name"])
# Tag for the image
IMAGE_VER = os.getenv("IMAGE_VER", f"{TOOL_CONFIG['version']}-py{PYTHON_VER}")
# Gather current working directory for Docker commands
PWD = os.getcwd()
# Local or Docker execution provide "local" to run locally without docker execution
INVOKE_LOCAL = is_truthy(os.getenv("INVOKE_LOCAL", False))  # pylint: disable=W1508
# Get project name from the toml file
PROJECT_NAME = PYPROJECT_CONFIG["tool"]["poetry"]["name"]
# Get current project version from the toml file
PROJECT_VERSION = PYPROJECT_CONFIG["tool"]["poetry"]["version"]


def docker_compose(context, command, **kwargs):
    """Helper function for running a specific docker-compose command with all appropriate parameters and environment.
    Args:
        context (obj): Used to run specific commands
        command (str): Command string to append to the "docker-compose ..." command, such as "build", "up", etc.
        **kwargs: Passed through to the context.run() call.
    """
    compose_command_tokens = [
        "docker-compose",
        f'--project-name "{context.batfish_routing.project_name}"',
        f'--project-directory "{context.batfish_routing.compose_dir}"',
    ]

    for compose_file in context.batfish_routing.compose_files:
        compose_file_path = os.path.join(context.batfish_routing.compose_dir, compose_file)
        compose_command_tokens.append(f'-f "{compose_file_path}"')

    compose_command_tokens.append(command)

    # If `service` was passed as a kwarg, add it to the end.
    service = kwargs.pop("service", None)
    if service is not None:
        compose_command_tokens.append(service)

    print(f'Running docker-compose command "{command}"')
    compose_command = " \\\n    ".join(compose_command_tokens)
    env = kwargs.pop("env", {})
    env.update({"PYTHON_VER": context.batfish_routing.python_ver})
    if "hide" not in kwargs:
        env_str = " \\\n    ".join(f"{var}={value}" for var, value in env.items())
        print(f"[dim]{env_str} \\\n    {compose_command}[/dim]")
    return context.run(compose_command, env=env, **kwargs)


def run_command(context, command, **kwargs):
    """Wrapper to run a command locally or inside the container."""
    if is_truthy(context.batfish_routing.local):
        print(f'Running command "{command}"')
        context.run(command, pty=True, **kwargs)
    else:
        docker_compose_status = "ps --services --filter status=running"
        results = docker_compose(context, docker_compose_status, hide="out")
        if "batfish_routing" in results.stdout:
            compose_command = f"exec batfish-routing {command}"
        else:
            compose_command = f"run --entrypoint '{command}' batfish-routing"

        docker_compose(context, compose_command, pty=True)


# ------------------------------------------------------------------------------
# BUILD
# ------------------------------------------------------------------------------
@task(
    help={
        "force_rm": "Always remove intermediate containers.",
        "cache": "Whether to use Docker's cache when building the image. (Default: enabled)",
        "poetry_parallel": "Enable/disable poetry to install packages in parallel. (Default: True)",
        "pull": "Whether to pull Docker images when building the image. (Default: disabled)",
    }
)
def build(context, force_rm=False, cache=True, poetry_parallel=True, pull=False):
    """Build batfish_routing docker image."""
    command = f"build --build-arg PYTHON_VER={context.batfish_routing.python_ver}"

    if not cache:
        command += " --no-cache"
    if force_rm:
        command += " --force-rm"
    if poetry_parallel:
        command += " --build-arg POETRY_PARALLEL=true"
    if pull:
        command += " --pull"

    print(f"Building batfish_routing with Python {context.batfish_routing.python_ver}...")
    docker_compose(context, command, env={"DOCKER_BUILDKIT": "1", "COMPOSE_DOCKER_CLI_BUILD": "1"})


# ------------------------------------------------------------------------------
# START / STOP / DEBUG
# ------------------------------------------------------------------------------
@task(help={"service": "If specified, only affect this service."})
def debug(context, service=None):
    """Start Batfish Routing and its dependencies in debug mode."""
    print("Starting Batfish Routing in debug mode...")
    docker_compose(context, "up", service=service)


@task(help={"service": "If specified, only affect this service."})
def start(context, service=None):
    """Start Batfish Routing and its dependencies in detached mode."""
    print("Starting Batfish Routing in detached mode...")
    docker_compose(context, "up --detach", service=service)


@task(help={"service": "If specified, only affect this service."})
def restart(context, service=None):
    """Gracefully restart containers."""
    print("Restarting Batfish Routing...")
    docker_compose(context, "restart", service=service)


@task(help={"service": "If specified, only affect this service."})
def stop(context, service=None):
    """Stop Batfish Routing and its dependencies."""
    print("Stopping Batfish Routing...")
    if not service:
        docker_compose(context, "down")
    else:
        docker_compose(context, "stop", service=service)


@task
def clean(context):
    """Remove the project specific image.
    Args:
        context (obj): Used to run specific commands
    """
    print(f"Attempting to forcefully remove image {IMAGE_NAME}:{IMAGE_VER}")
    context.run(f"docker rmi {IMAGE_NAME}:{IMAGE_VER} --force")
    print(f"Successfully removed image {IMAGE_NAME}:{IMAGE_VER}")


@task
def rebuild(context):
    """Clean the Docker image and then rebuild without using cache.
    Args:
        context (obj): Used to run specific commands
    """
    clean(context)
    build(context)

@task
def yamllint(context):
    """Run yamllint to validate formatting adheres to NTC defined YAML standards.
    Args:
        context (obj): Used to run specific commands
        local (bool): Define as `True` to execute locally
    """
    exec_cmd = "yamllint ."
    run_command(context, exec_cmd)


@task
def generate_configurations(context):
    """Run ansible playbook to generate configurations
    Args:
        context (obj): Used to run specific commands
        local (bool): Define as `True` to execute locally
    """
    exec_cmd = "ansible-playbook /local/config_gen/pb_generate_configs.yml -i /local/config_gen/inventory.yml"
    run_command(context, exec_cmd)


@task
def test_configurations(context):
    """Run ansible playbook to generate configurations
    Args:
        context (obj): Used to run specific commands
        local (bool): Define as `True` to execute locally
    """
    exec_cmd = "python /local/config_gen/tests/test_routing.py"
    run_command(context, exec_cmd)


@task(help={"service": "Name of the service to shell into"})
def cli(context, service="batfish-routing"):
    """Launch a bash shell inside the running batfish-routing (or other) Docker container."""
    docker_compose(context, f"exec {service} bash", pty=True)


@task
def tests(context):
    """Run all linters and unit tests."""
    yamllint(context)
    generate_configurations(context)
    test_configurations(context)
    print("All tests have passed!")
