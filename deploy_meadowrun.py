import asyncio
import meadowrun
from scrape import main_remote


if __name__ == "__main__":
    QUERY = "beautiful"

    asyncio.run(
        meadowrun.run_function(
            main_remote,
            meadowrun.AllocEC2Instance("eu-west-2"),
            meadowrun.Resources(logical_cpu=1, memory_gb=4, max_eviction_rate=80),
            meadowrun.Deployment.git_repo(
                "https://github.com/torphix/quick_scrape.git",
                interpreter=meadowrun.PipRequirementsFile(
                    "requirements.txt",
                    python_version="3.8",
                    additional_software=[
                        "python-tk",
                        "wget",
                        "curl",
                        "unzip",
                        "rpm",
                        "libglib2.0-0",
                        "libnss3",
                        "libgconf-2-4",
                        "libfontconfig1",
                        "fonts-liberation ",
                        "libasound2",
                        "libatk-bridge2.0-0",
                        "libatk1.0-0",
                        "libatspi2.0-0",
                        "libcairo2",
                        "libcups2",
                        "libdrm2",
                        "libgbm1",
                        "libu2f-udev",
                        "libvulkan1",
                        "libxcomposite1",
                        "libxdamage1",
                        "libxfixes3",
                        "libxkbcommon0",
                        "libxrandr2",
                        "xdg-utils",
                    ],
                ),
            ),
            args=["beautiful"],
        )
    )
