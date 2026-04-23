def parse_price(raw: str) -> float:
    """Убирает символ фунта и пробелы, возвращает float."""
    return float(raw.replace('£', '').strip())
 
def parse_rating(css_class: str, rating_map: dict) -> int:
    """Из строки класса 'star-rating Three' извлекает число 3."""
    word = css_class.split()[1]          # 'Three'
    return rating_map.get(word, 0)
 
def parse_in_stock(text: str) -> bool:
    """Возвращает True если текст содержит 'In stock'."""
    return 'In stock' in text

