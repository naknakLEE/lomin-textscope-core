#!/bin/bash
# TODO 각프로젝트마다 다르게 설정

cd /home/lomin/Circleci/textscope-client/textscope-evaluator

for dir in $(ls /home/lomin/Circleci/sample/$BSN_CODE); do
    echo "Sample dir: $dir"
    python3 tools/textscope_eval/textscope_requester.py \
        --textscope-url http://localhost:9100 \
        --input-dir /home/lomin/Circleci/sample/$BSN_CODE/$dir \
        --output-dir /home/lomin/Circleci/result/$BSN_CODE/$dir \
        --endpoint-type kv \
        --doc-type KBC3-01 \
        --business-code kbc3 \
        --textscope-eval-config ./tools/textscope_eval/textscope_eval_config_kbc3.json &&

    python3 -m tools.textscope_eval.textscope_exporter \
        --input-dir /home/lomin/Circleci/result/$BSN_CODE/$dir/inference_outputs \
        --output-dir /home/lomin/Circleci/result/$BSN_CODE/$dir/excel \
        --business-code kbc3 \
        --textscope-eval-config ./tools/textscope_eval/textscope_eval_config_kbc3.json &&

    python3 tools/textscope_eval/textscope_evaluator.py \
        --textscope-output-xlsx /home/lomin/Circleci/result/$BSN_CODE/$dir/excel/kv_result.xlsx \
        --gt-xlsx /home/lomin/Circleci/gt/$BSN_CODE/$dir/${dir}_gt.xlsx \
        --output-dir /home/lomin/Circleci/result/$BSN_CODE/$dir/ \
        --business-code kbc3 \
        --textscope-eval-config ./tools/textscope_eval/textscope_eval_config_kbc3.json
done
