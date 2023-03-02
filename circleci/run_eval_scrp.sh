#!/bin/bash
# TODO 각프로젝트마다 다르게 설정

BSN_CODE=$1

cd ~/Circleci/textscope-client/textscope-evaluator

for dir in $(ls ~/Circleci/sample/$BSN_CODE); do
    echo "Sample dir: $dir"
    doc_type=`cat tools/textscope_eval/convert_bsn_code.json | jq ".\"$BSN_CODE\".\"$dir\""`
    python3 tools/textscope_eval/textscope_requester.py \
        --textscope-url http://localhost:9900 \
        --input-dir /home/lomin/Circleci/sample/$BSN_CODE/$dir \
        --output-dir /home/lomin/Circleci/result/$BSN_CODE/$dir \
        --endpoint-type cls-kv \
        --doc-type $doc_type \
        --business-code $BSN_CODE \
        --textscope-eval-config ./tools/textscope_eval/textscope_eval_config_${BSN_CODE}.json &&

    python3 -m tools.textscope_eval.textscope_exporter \
        --input-dir /home/lomin/Circleci/result/$BSN_CODE/$dir/inference_outputs \
        --output-dir /home/lomin/Circleci/result/$BSN_CODE/$dir/excel \
        --business-code $BSN_CODE \
        --textscope-eval-config ./tools/textscope_eval/textscope_eval_config_${BSN_CODE}.json &&

    python3 tools/textscope_eval/textscope_evaluator.py \
        --textscope-output-xlsx /home/lomin/Circleci/result/$BSN_CODE/$dir/excel/kv_result.xlsx \
        --gt-xlsx /home/lomin/Circleci/gt/$BSN_CODE/$dir/${dir}_gt.xlsx \
        --output-dir /home/lomin/Circleci/result/$BSN_CODE/$dir/ \
        --business-code $BSN_CODE \
        --textscope-eval-config ./tools/textscope_eval/textscope_eval_config_${BSN_CODE}.json
done
