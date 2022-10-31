#!/bin/bash

read -p "치환 할 폴더명(폴더 안에 파일들을 모두 찾아 치환합니다. ex. assets):" folder_path

read -p "기존 내용:" origin_txt

read -p "변결할 내용:" new_txt


echo "$origin_txt 검색 결과: "
grep -o "$origin_txt" $folder_path/*
count=$(grep -o "$origin_txt" $folder_path/* | wc -l)
echo "$origin_txt 개수: $count" 

sed -i "s/$origin_txt/$new_txt/g" $folder_path/*

echo "변경 완료"