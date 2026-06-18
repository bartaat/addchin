from addchin import chinese


def test_to_traditional():
    assert chinese.to_traditional("图书馆") == "圖書館"


def test_to_pinyin():
    assert chinese.to_pinyin("朋友") == "péng yǒu"
