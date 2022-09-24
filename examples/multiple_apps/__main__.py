from multiple_apps import local, sagemaker

import pydantic_argparse

app = pydantic_argparse.PydanticCLIApp()

app.add_application(local.app)
app.add_application(sagemaker.app)


if __name__ == "__main__":
    app()
