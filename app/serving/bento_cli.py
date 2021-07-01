from bentoml.server import start_dev_server, start_prod_server

saved_bundle_path = "/root/bentoml/repository/DocumentModelService/20210701121452_94211E"
port = 5000


# start_dev_server(
#     saved_bundle_path,
#     port=port,
#     mb_max_batch_size=None,
#     mb_max_latency=None,
#     run_with_ngrok=None,
#     enable_swagger=True,
# )

start_prod_server(
    saved_bundle_path,
    port=port,
    # workers: Optional[int] = None,
    # timeout: Optional[int] = None,
    # enable_swagger: Optional[bool] = None,
    # mb_max_batch_size: Optional[int] = None,
    # mb_max_latency: Optional[int] = None,
    # microbatch_workers: Optional[int] = None,
)
