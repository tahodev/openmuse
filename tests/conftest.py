def pytest_addoption(parser):
    parser.addoption(
        "--update-example-snapshots",
        action="store_true",
        help="rewrite the expected output snapshots after reviewing intentional example changes",
    )
