def compare_hex_files(file1_path, file2_path):
    """
    두 개의 공백 및 줄바꿈으로 구분된 HEX 텍스트 파일을 비교하여 일치율을 출력한다.
    """
    try:
        # 파일 읽기 및 토큰화 (공백 + 줄바꿈 기준)
        with open(file1_path, 'r') as f1:
            tokens1 = f1.read().split()

        with open(file2_path, 'r') as f2:
            tokens2 = f2.read().split()

        len1 = len(tokens1)
        len2 = len(tokens2)
        min_len = min(len1, len2)
        max_len = max(len1, len2)

        # 값 비교
        mismatch_indices = []
        match_count = 0

        for i in range(min_len):
            if tokens1[i].upper() == tokens2[i].upper():
                match_count += 1
            else:
                mismatch_indices.append((i, tokens1[i], tokens2[i]))

        total_tokens = max_len
        match_ratio = match_count / total_tokens * 100

        print("📊 비교 결과 요약")
        print(f"총 토큰 수 (최대 기준): {total_tokens}")
        print(f"일치한 토큰 수: {match_count}")
        print(f"불일치한 토큰 수: {len(mismatch_indices)}")
        print(f"일치율: {match_ratio:.2f}%")

        if len1 != len2:
            print(f"⚠️ 두 파일의 길이가 다릅니다: file1={len1}개, file2={len2}개")

        # 일부 mismatch 출력
        if mismatch_indices:
            print("\n❌ 불일치 항목 (최대 10개):")
            for i, val1, val2 in mismatch_indices[:10]:
                print(f" - 인덱스 {i}: file1='{val1}' vs file2='{val2}'")

    except Exception as e:
        print(f"오류 발생: {e}")

compare_hex_files(
    "expanding_output_frame1.txt",
    "compare_txt/dog_layer7_expand_output_hex_rearranged.txt"
)
compare_hex_files(
    "expanding_output_frame2.txt",
    "compare_txt/rock_layer7_expand_output_hex_rearranged.txt"
)
