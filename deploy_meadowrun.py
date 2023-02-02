import asyncio
import meadowrun
from scrape import main_remote

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
                additional_software=["python-tk", "wget", "curl", "unzip", "rpm"],
            ),
        ),
        args=["beautiful"],
    )
)
