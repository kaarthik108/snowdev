import click
from termcolor import colored

from snowdev import SnowBot, SnowHelper
from snowdev.deployment import DeploymentArguments, DeploymentManager


@click.group()
@click.pass_context
def cli(ctx):
    """Deploy Snowflake UDFs, Stored Procedures and Streamlit apps."""
    ctx.ensure_object(dict)


@cli.command()
def init():
    """Initialize the project structure."""
    DeploymentManager.create_directory_structure()


@cli.command()
@click.option("--udf", type=str, help="The name of the udf.")
@click.option("--sproc", type=str, help="The name of the stored procedure.")
@click.option("--streamlit", type=str, help="The name of the streamlit app.")
def new(udf, sproc, streamlit):
    """Create a new component."""
    args_dict = {"udf": udf, "sproc": sproc, "streamlit": streamlit}
    SnowHelper.create_new_component(args_dict)


@cli.command()
@click.option("--udf", type=str, help="The name of the udf.")
@click.option("--sproc", type=str, help="The name of the stored procedure.")
def test(udf, sproc):
    """Test the deployment."""
    deployment_args = DeploymentArguments(udf=udf, sproc=sproc)
    manager = DeploymentManager(deployment_args)
    manager.test_locally()


@cli.command()
def upload():
    """Upload static content."""
    manager = DeploymentManager()
    manager.upload_static()


@cli.command()
@click.option("--package", type=str, help="Name of the package to zip and upload.")
def add(package):
    """Add a package and optionally upload."""
    manager = DeploymentManager()
    user_response = input(
        colored("🤔 Do you want to upload the zip to stage? (yes/no): ", "cyan")
    )

    if user_response.lower() in ["yes", "y"]:
        manager.deploy_package(package, upload=True)
    else:
        manager.deploy_package(package, upload=False)


@cli.command()
@click.option("--udf", type=str, help="The name of the udf.")
@click.option("--sproc", type=str, help="The name of the stored procedure.")
@click.option("--streamlit", type=str, help="The name of the streamlit app.")
@click.option("--embed", is_flag=True, help="Run the embeddings.")
def ai(udf, sproc, streamlit, embed):
    """AI commands."""

    if embed:
        print(colored("Initializing AI...\n", "cyan"))
        SnowBot.ai_embed()
        return

    component_type, prompt = None, None

    if udf:
        component_type = "udf"
        prompt = udf
    elif sproc:
        component_type = "sproc"
        prompt = sproc
    elif streamlit:
        component_type = "streamlit"
        prompt = streamlit

    if not component_type:
        print(
            colored(
                "⚠️ Please specify a type (--udf, --sproc, or --streamlit) along with the ai command.",
                "yellow",
            )
        )
        return

    component_name = input(
        colored(f"🤔 Enter the {component_type.upper()} name: ", "cyan")
    )

    if SnowBot.component_exists(component_name, component_type):
        print(
            colored(
                f"⚠️ Component named {component_name} already exists! Choose another name or check your directories.",
                "yellow",
            )
        )
        return

    SnowBot.create_new_ai_component(
        component_name, prompt, template_type=component_type
    )


@cli.command()
@click.option("--sproc", type=str, help="The name of the stored procedure.")
@click.option("--udf", type=str, help="The name of the udf.")
@click.option("--streamlit", type=str, help="The name of the streamlit app.")
def deploy(sproc, udf, streamlit):
    """Deploy components."""
    arguments = {"sproc": sproc, "udf": udf, "streamlit": streamlit}
    args = DeploymentArguments(**arguments)
    manager = DeploymentManager(args)
    manager.main()


if __name__ == "__main__":
    cli()
