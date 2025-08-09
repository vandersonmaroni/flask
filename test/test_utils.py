from app.utils import format_currency

def test_format_currency_with_decimals():
    """
    Garante que a função formata corretamente um número
    que já possui casas decimais.
    """
    # Padrão Arrange-Act-Assert
    # Arrange (Preparação): Define a entrada.
    input_value = 59.9
    
    # Act (Ação): Executa a função a ser testada.
    result = format_currency(input_value)
    
    # Assert (Verificação): Verifica se a saída é a esperada.
    assert result == "R$ 59,90"


def test_format_currency_with_integer():
    """
    Garante que a função adiciona as casas decimais
    corretamente a um número inteiro.
    """
    assert format_currency(123) == "R$ 123,00"


def test_format_currency_with_zero():
    """
    Garante que a função lida corretamente com o valor zero.
    """
    assert format_currency(0) == "R$ 0,00"