# 기본 설정값
DEFAULT_CONFIG = {
    "template_threshold": 0.9,
    "hash_threshold": 0.95,
    "overlap_threshold": 0.1,
    "scales": [1.0],
    "stride": 1,
}

# 지원하는 이미지 형식
SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}

# 매칭 방법들
AVAILABLE_METHODS = [
    "template",  # OpenCV 템플릿 매칭
    "hash",  # 해시 기반 매칭
    "multi_scale",  # 다중 스케일 템플릿 매칭
    "edge",  # 엣지 기반 매칭
    "color",  # 색상 기반 매칭
    "robust",  # 여러 방법 조합
]

# 해시 방법들
HASH_METHODS = ["ahash", "phash", "dhash"]

# 성능 최적화 설정
PERFORMANCE_CONFIG = {
    "max_image_size": (4000, 4000),  # 최대 처리 이미지 크기
    "min_template_size": (10, 10),  # 최소 템플릿 크기
    "default_stride": 10,  # 기본 슬라이딩 간격
    "batch_size": 50,  # 배치 처리 크기
    "early_stop": False,  # 매칭되는 즉시 종료 여부
}

# matchers 의 match 함수의 config
MATCHERS_CONFIG = {
    "except_overlap": True, # 매칭 중 겹치는 부분 제거
}