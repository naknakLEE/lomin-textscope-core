```bash
workspace
├── app
│   ├── common
│   │   ├── config.py
│   │   └── const.py
│   ├── database
│   │   ├── connection.py
│   │   ├── create_table.txt
│   │   ├── crud
│   │   │   ├── base.py
│   │   │   ├── crud_log.py
│   │   │   ├── crud_usage.py
│   │   │   └── crud_user.py
│   │   └── schema.py
│   ├── errors
│   │   └── exceptions.py
│   ├── main.py
│   ├── middlewares
│   │   ├── exception_handler.py
│   │   ├── logging.py
│   │   └── timeout_handling.py
│   ├── models.py
│   ├── outputs
│   │   └── idcard
│   │       └── test.png
│   ├── routes
│   │   ├── admin.py
│   │   ├── auth.py
│   │   ├── index.py
│   │   ├── inference.py
│   │   └── users.py
│   ├── schemas.py
│   └── utils
│       ├── async_multiple_request_testing.py
│       ├── auth.py
│       ├── create_app.py
│       ├── logger.py
│       ├── logging.py
│       ├── profiling.py
│       ├── pytinstrument_result.html
│       └── utils.py
├── assets
│   ├── apply-thales.sh
│   ├── dummy_results.npy
│   ├── envelop_serving_files.sh
│   ├── grafana
│   │   ├── bentoml-dashboard-docker-swarm-1623677587070.json
│   │   ├── MySQL Overview-1629934580287.json
│   │   ├── NGINX-1629934774789.json
│   │   ├── node-exporter-full_rev23.json
│   │   └── NVIDIA DCGM Exporter Dashboard-1629934231003.json
│   ├── idcard.json
│   ├── init_file_generator.py
│   ├── kakaobank.json
│   ├── kbcard.json
│   ├── load-textscope-images.sh
│   ├── remove-textscope-related-image-and-volume-and-network.sh
│   ├── saved_dir
│   ├── save-image-to-local.sh
│   ├── stop_gunicorn.sh
│   └── thales
│       ├── DEMOMA.hvc
│       ├── linuxenv
│       ├── TBXBG-10223672 2021-07-28 22.51.v2c
│       └── TBXBG.hvc
├── azure-pipelines.yml
├── .bandit
├── build.sh
├── .coverage
├── database
│   └── my.cnf
├── data.pickle
├── directory_tree.txt
├── docker
│   ├── base
│   │   ├── Dockerfile.gpu_serving
│   │   ├── Dockerfile.pp
│   │   ├── Dockerfile.serving
│   │   ├── Dockerfile.web
│   │   └── Dockerfile.wrapper
│   ├── build
│   │   ├── Dockerfile.gpu_serving
│   │   ├── Dockerfile.pp
│   │   ├── Dockerfile.web
│   │   └── Dockerfile.wrapper
│   ├── production
│   │   ├── Dockerfile.gpu_serving
│   │   ├── Dockerfile.mysql
│   │   ├── Dockerfile.nginx
│   │   ├── Dockerfile.pp
│   │   ├── Dockerfile.web
│   │   └── Dockerfile.wrapper
│   └── temp
│       ├── Dockerfile.base
│       ├── Dockerfile.gpu_serving
│       ├── Dockerfile.pp
│       ├── Dockerfile.redoc
│       ├── Dockerfile.serving
│       └── Dockerfile.web
├── docker-compose.base.yml
├── docker-compose.build.yml
├── docker-compose.dev.yml
├── docker-compose.prod.test.yml
├── docker-compose.prod.yml
├── docker-compose.yml
├── .dockerignore
├── .env
├── .flake8
├── .gitignore
├── .gitmodules
├── inference_server
│   ├── assets
│   │   ├── bentoml_configuration.yml
│   │   ├── bentoml-for-health-check
│   │   │   ├── configuration
│   │   │   │   ├── containers.py
│   │   │   │   └── default_configuration.yml
│   │   │   ├── health
│   │   │   │   └── health.py
│   │   │   ├── marshal
│   │   │   │   ├── dispatcher.py
│   │   │   │   ├── marshal.py
│   │   │   │   └── utils.py
│   │   │   ├── metrics
│   │   │   │   └── prometheus.py
│   │   │   ├── server
│   │   │   │   ├── gunicorn_config.py
│   │   │   │   ├── gunicorn_health_server.py
│   │   │   │   ├── gunicorn_marshal_server.py
│   │   │   │   ├── gunicorn_model_server.py
│   │   │   │   ├── instruments.py
│   │   │   │   ├── model_app.py
│   │   │   │   └── static_content
│   │   │   │       ├── main.css
│   │   │   │       ├── marked.min.js
│   │   │   │       ├── readme.css
│   │   │   │       ├── swagger-ui-bundle.js
│   │   │   │       └── swagger-ui.css
│   │   │   └── utils
│   │   │       ├── alg.py
│   │   │       ├── benchmark.py
│   │   │       ├── cloudpickle.py
│   │   │       ├── csv.py
│   │   │       ├── dataclasses.py
│   │   │       ├── dataframe_util.py
│   │   │       ├── docker_utils.py
│   │   │       ├── flask_ngrok.py
│   │   │       ├── gcs.py
│   │   │       ├── hybridmethod.py
│   │   │       ├── lazy_loader.py
│   │   │       ├── log.py
│   │   │       ├── open_api.py
│   │   │       ├── ruamel_yaml.py
│   │   │       ├── s3.py
│   │   │       ├── tempdir.py
│   │   │       ├── tensorflow.py
│   │   │       └── usage_stats.py
│   │   ├── document_classification
│   │   │   ├── 1
│   │   │   │   ├── lo_best_checkpoint.onnx
│   │   │   │   └── lo_best_checkpoint.ts
│   │   │   ├── 2
│   │   │   │   └── best_checkpoint.ts
│   │   │   └── support_set
│   │   │       └── features.pkl
│   │   ├── document_detection
│   │   │   └── 1
│   │   │       ├── gocr_chshin_bankbook_mask_rcnn_E_B3_BiFPN_model_0087499_f1=96.7552.ts
│   │   │       └── gocr_chshin_efficientdet_d4_210607_model_0169999_F1_93.ts
│   │   ├── gulim.ttc
│   │   ├── id_boundary
│   │   │   └── 1
│   │   │       └── kb_201027_skkang_002_id_outline_mask_0195000_b1.onnx
│   │   ├── idcard.json
│   │   ├── id_kv
│   │   │   ├── 1
│   │   │   │   ├── kb_201016_skkang_001_id_kv_0069000_b1.onnx
│   │   │   │   └── model_0074999_precision=93.3406-batch=1.ts
│   │   │   ├── 2
│   │   │   │   └── model_0084999_precision=94.1574-batch=1.ts
│   │   │   ├── 3
│   │   │   │   └── vladimir_model_0037499_recall=88.9870-batch=1.ts
│   │   │   ├── 4
│   │   │   │   └── gocr_chshin_idcard_mask_rcnn_E_B3_BiFPN_model_0037499_recall=88.9870-batch=1.ts
│   │   │   └── 5
│   │   │       └── gocr_chshin_idcard_mask_rcnn_E_B3_BiFPN_model_0132499_f1=97.6354-batch=1.ts
│   │   ├── kbcard.json
│   │   ├── kbcard_kv
│   │   │   ├── 1
│   │   │   │   ├── dhson_cbr_efficientdet_d3_model_0089999.ts
│   │   │   │   ├── gocr_chshin_bankbook_mask_rcnn_E_B3_BiFPN_model_0087499_f1=96.7552.ts
│   │   │   │   └── gocr_chshin_cbr_efficientdet_d3_model_0197499_f1=88.2821.ts
│   │   │   ├── 2
│   │   │   │   ├── gocr_chshin_bankbook_mask_rcnn_E_B3_BiFPN_model_0032499_f1=86.7542-batch=1.ts
│   │   │   │   └── gocr_chshin_cbr_efficientdet_d3_model_0022499_f1=96.1749-batch=1.ts
│   │   │   ├── 3
│   │   │   │   └── gocr_chshin_bankbook_mask_rcnn_E_B3_BiFPN_version6_model_0077499_f1=88.3529-batch=1.ts
│   │   │   └── 4
│   │   │       └── skjung_bankbook_mask_rcnn_X_101_32x8d_FPN_3x_model_0079999_f1=94.0219.ts
│   │   ├── modified_bentoml_file
│   │   │   ├── kakaobank_loader.py
│   │   │   ├── kbcard_loader.py
│   │   │   ├── onnx.py
│   │   │   ├── pip_pkg.py
│   │   │   └── pytorch.py
│   │   ├── recognizer
│   │   │   ├── 1
│   │   │   │   ├── general_200702_skjung_001_rec.ts
│   │   │   │   └── kb_201109_skkang_001_id_rec_0020000_b9.onnx
│   │   │   ├── 2
│   │   │   │   └── 210910_gocr_di_transformer_base_epoch=0-acc=0.934-928c7794.ts
│   │   │   └── 3
│   │   │       └── 210913_gocr_di_transformer_base_epoch=0-acc=0.939-928c7794.ts
│   │   ├── request_ocr.py
│   │   ├── rotate
│   │   │   └── 1
│   │   │       └── rotator_model.onnx
│   │   ├── textscope_kakaobank.json
│   │   └── textscope_kbcard.json
│   ├── .bandit
│   ├── docker-compose.yml
│   ├── Dockerfile.gpu_serving
│   ├── .env
│   ├── .flake8
│   ├── .gitignore
│   ├── .gitmodules
│   ├── inference_server
│   │   ├── common
│   │   │   ├── config.py
│   │   │   └── const.py
│   │   ├── encrytion.py
│   │   ├── errors
│   │   │   └── exceptions.py
│   │   ├── generate_idcard_model_service.py
│   │   ├── generate_kakaobank_model_service.py
│   │   ├── generate_kbcard_model_service.py
│   │   ├── generate_new_kbcard_model_service.py
│   │   ├── idcard_model_service.py
│   │   ├── kakaobank_model_service.py
│   │   ├── kbcard_model_service.py
│   │   ├── minio_test.py
│   │   └── utils
│   │       ├── azure_blob_container
│   │       │   ├── download_blob_to_local.py
│   │       │   └── upload_blob_to_azure.py
│   │       ├── catalogs.py
│   │       ├── debugging.py
│   │       ├── envs.py
│   │       ├── infer.py
│   │       ├── parser.py
│   │       ├── post_processing.py
│   │       ├── pre_processing.py
│   │       └── utils.py
│   ├── README.md
│   ├── requirments-serving.txt
│   ├── setup.py
│   └── tox.ini
├── kakaobank_wrapper
│   ├── app
│   ├── assets
│   │   └── load_test.py
│   ├── .bandit
│   ├── .flake8
│   ├── .gitignore
│   ├── kakaobank_wrapper
│   │   ├── app
│   │   │   ├── common
│   │   │   │   ├── config.py
│   │   │   │   └── const.py
│   │   │   ├── database
│   │   │   │   ├── connection.py
│   │   │   │   ├── crud
│   │   │   │   │   ├── base.py
│   │   │   │   │   ├── crud_log.py
│   │   │   │   │   ├── crud_usage.py
│   │   │   │   │   └── crud_user.py
│   │   │   │   ├── multiprocessing_manager.py
│   │   │   │   └── schema.py
│   │   │   ├── errors
│   │   │   │   └── exceptions.py
│   │   │   ├── main.py
│   │   │   ├── middlewares
│   │   │   │   ├── custom_exception.py
│   │   │   │   └── logging.py
│   │   │   ├── models.py
│   │   │   ├── routes
│   │   │   │   ├── index.py
│   │   │   │   └── ocr.py
│   │   │   └── utils
│   │   │       ├── create_app.py
│   │   │       ├── logging.py
│   │   │       ├── ocr_request_inspector.py
│   │   │       ├── ocr_response_parser.py
│   │   │       ├── ocr_result_inspector.py
│   │   │       ├── ocr_result_parser.py
│   │   │       ├── request_form_parser.py
│   │   │       ├── save_data.py
│   │   │       └── utils.py
│   │   └── tests
│   │       ├── api
│   │       │   └── test_ocr.py
│   │       ├── conftest.py
│   │       ├── testing.py
│   │       └── utils
│   │           ├── user.py
│   │           └── utils.py
│   ├── README.md
│   ├── setup.py
│   └── tox.ini
├── kbcard_wrapper
│   ├── assets
│   │   ├── convert_png_to_tiff.py
│   │   ├── convert_tiff_to_tiff.py
│   │   ├── Dockerfile
│   │   ├── Dockerfile.save
│   │   ├── idcard.json
│   │   ├── kbcard_setup.sh
│   │   ├── load_test.py
│   │   ├── mapping_feature_key.py
│   │   ├── mock-up.py
│   │   └── test_ocr.py
│   ├── .bandit
│   ├── .flake8
│   ├── .gitignore
│   ├── kbcard_wrapper
│   │   ├── app
│   │   │   ├── common
│   │   │   │   ├── config.py
│   │   │   │   └── const.py
│   │   │   ├── database
│   │   │   │   ├── connection.py
│   │   │   │   ├── crud
│   │   │   │   │   ├── base.py
│   │   │   │   │   ├── crud_log.py
│   │   │   │   │   ├── crud_usage.py
│   │   │   │   │   └── crud_user.py
│   │   │   │   └── schema.py
│   │   │   ├── errors
│   │   │   │   └── exceptions.py
│   │   │   ├── main.py
│   │   │   ├── middlewares
│   │   │   │   ├── exception_handler.py
│   │   │   │   └── logging.py
│   │   │   ├── models.py
│   │   │   ├── routes
│   │   │   │   ├── index.py
│   │   │   │   └── ocr.py
│   │   │   └── utils
│   │   │       ├── create_app.py
│   │   │       ├── logging.py
│   │   │       ├── ocr_all_file.py
│   │   │       ├── ocr_response_parsing.py
│   │   │       └── request_parser.py
│   │   ├── schemas.py
│   │   └── tests
│   │       ├── api
│   │       │   └── test_ocr.py
│   │       ├── conftest.py
│   │       └── utils
│   │           ├── user.py
│   │           └── utils.py
│   ├── README.md
│   ├── setup.py
│   └── tox.ini
├── ldap
│   ├── grafana.ini
│   └── ldap.toml
├── lovit
│   ├── .gitignore
│   ├── lovit
│   │   ├── crypto
│   │   │   ├── crypto.py
│   │   │   ├── decipher.py
│   │   │   ├── decrypt.py
│   │   │   ├── encrypt.py
│   │   │   ├── key_gen.py
│   │   │   ├── solver.py
│   │   │   └── utils.py
│   │   ├── evaluation
│   │   │   └── via_eval.py
│   │   ├── modeling
│   │   ├── postprocess
│   │   │   ├── common.py
│   │   │   ├── document.py
│   │   │   ├── idcard.py
│   │   │   └── template.py
│   │   ├── preprocess
│   │   │   ├── aggamoto.py
│   │   │   ├── augmentation_impl.py
│   │   │   ├── augmentation.py
│   │   │   ├── recognition.py
│   │   │   └── transform.py
│   │   ├── profiling
│   │   ├── resources
│   │   │   ├── document
│   │   │   │   ├── nhis_cp.json
│   │   │   │   ├── nhis_cqa.json
│   │   │   │   ├── nhis_cq.json
│   │   │   │   └── nts_ci.json
│   │   │   ├── id
│   │   │   │   └── arc_nationality_en.txt
│   │   │   └── labels
│   │   │       ├── basic_symbol.txt
│   │   │       ├── digits.txt
│   │   │       ├── eng_capital.txt
│   │   │       ├── eng_lower.txt
│   │   │       ├── kor_2350.txt
│   │   │       ├── kor_jamo.txt
│   │   │       ├── mlt_all.txt
│   │   │       ├── numbers.txt
│   │   │       ├── symbols_extended.txt
│   │   │       └── symbols.txt
│   │   ├── structures
│   │   │   ├── bbox_ops.py
│   │   │   ├── catalogs.py
│   │   │   ├── document.py
│   │   │   └── keyvalue_dict.py
│   │   ├── utils
│   │   │   ├── converter.py
│   │   │   ├── descriptor_mathcer.py
│   │   │   ├── eval_utils.py
│   │   │   ├── miscellaneous.py
│   │   │   └── postprocess_utils.py
│   │   ├── __version__.py
│   │   └── visualization
│   │       └── visualizer.py
│   ├── README.md
│   ├── requirements.txt
│   └── setup.py
├── mysql.conf
│   ├── my.cnf
│   └── mysql-cluster.cnf
├── openldap
│   ├── docker-compose.yaml
│   ├── Dockerfile
│   ├── entrypoint.sh
│   ├── ldap.conf
│   ├── ldap_dev.toml
│   ├── ldap_posix_dev.toml
│   ├── modules
│   │   └── memberof.ldif
│   ├── notes.md
│   ├── prepopulate
│   │   ├── 1_units.ldif
│   │   ├── 2_users.ldif
│   │   └── 3_groups.ldif
│   └── prepopulate.sh
├── pp_server
│   ├── assets
│   │   └── basic_cert_boxlist_data.pickle
│   ├── .gitignore
│   ├── pp_server
│   │   └── app
│   │       ├── common
│   │       │   ├── config.py
│   │       │   └── const.py
│   │       ├── database
│   │       │   └── connection.py
│   │       ├── main.py
│   │       ├── main.spec
│   │       ├── postprocess
│   │       │   ├── bankbook.py
│   │       │   ├── basic_cert.py
│   │       │   ├── ccr.py
│   │       │   ├── commons.py
│   │       │   ├── family_cert.py
│   │       │   ├── idcard.py
│   │       │   ├── kbcard.py
│   │       │   ├── regi_cert.py
│   │       │   ├── rrtable.py
│   │       │   └── seal_imp_cert.py
│   │       ├── routes
│   │       │   ├── document.py
│   │       │   ├── index.py
│   │       │   └── kv.py
│   │       ├── structures
│   │       │   ├── bounding_box.py
│   │       │   └── keyvalue_dict.py
│   │       └── utils
│   │           ├── catalogs.py
│   │           ├── create_app.py
│   │           ├── logging.py
│   │           └── utils.py
│   └── setup.py
├── prometheus.yml
├── proxy
│   ├── certificate
│   │   ├── default
│   │   ├── nginx-certificate.crt
│   │   └── nginx.key
│   ├── multiple_gpu_load_balancing.conf
│   ├── nginx.conf
│   ├── nginx.vh.default.conf
│   └── tpl
│       ├── 10-listen-on-ipv6-by-default.sh
│       ├── 20-envsubst-on-templates.sh
│       ├── docker-entrypoint.sh
│       └── Makefile
├── README.md
├── requirments
│   ├── requirments-kakaobank.txt
│   ├── requirments-kbcard.txt
│   ├── requirments-lint.txt
│   ├── requirments-pp.txt
│   ├── requirments-serving.txt
│   ├── requirments-test.txt
│   └── requirments-web.txt
├── setup.py
├── tests
│   ├── api
│   │   ├── test_login.py
│   │   └── test_users.py
│   ├── conftest.py
│   ├── crud
│   │   └── test_db_users.py
│   └── utils
│       ├── user.py
│       └── utils.py
└── tox.ini

144 directories, 434 files
```
