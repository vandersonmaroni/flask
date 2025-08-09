def format_currency(value: float) -> str:
    """
    Formata um valor numérico (float) para uma string de moeda
    no padrão de Reais (R$).

    Exemplo de uso:
    >>> format_currency(29.9)
    'R$ 29,90'
    """
    return f"R$ {value:.2f}".replace('.', ',')