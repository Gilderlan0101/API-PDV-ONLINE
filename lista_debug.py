methods = {
    'Pix': [{'Product_name': '', 'amount': '', 'date': '', 'employee': ''}],
    'Cartão': [{'Product_name': '', 'amount': '', 'date': '', 'employee': ''}],
    'Dinheiro': [{'Product_name': '', 'amount': '', 'date': '', 'employee': ''}],
    'Nota': [{'Product_name': '', 'amount': '', 'date': '', 'employee': ''}],
    'Fiado': [{'Product_name': '', 'amount': '', 'date': '', 'employee': ''}],
}
methods['Pix'][0]['Product_name'] = 'teste'
print(len(methods['Pix']))
