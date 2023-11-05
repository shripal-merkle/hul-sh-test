from flask import Flask, request, jsonify, render_template
import cv2
import pytesseract
import re
import numpy
import json

with open('constants/products.json', 'r') as json_file:
    products = json.load(json_file)

with open('constants/units.json', 'r') as json_file:
    units = json.load(json_file)

all_units = (units['weight_units'] 
+ units['weight_variations'] 
+ units['volume_units'] 
+ units['volume_variations'])


app = Flask(__name__)

# def elimination(array, extraction):


def extractProductFromArray(row):
    from difflib import get_close_matches
    given_string = ' '.join(row)
    closest_product = get_close_matches(given_string, products, n=1, cutoff=0.33)
    return closest_product[0] if len(closest_product)>0 else 'Could not found the product'


def extractUnitFromArray(row):
    pattern = r'(\d+(?:\.\d+)?)\s*([A-Za-z]+)'
    text = ' '.join(row)
    match = re.search(pattern, text)

    if match:
        value = match.group(1)
        unit = match.group(2)
        return f"{value} {unit}"

    return None


def extractQuantityFromArray(row):
    for element in row:
        element = element.replace('O', '0').replace('o', '0').replace('.', '').replace(' ', '')  # Remove 'O', 'o', and periods
        if element.isdigit():
            return int(element)
    return None



@app.route('/')
def upload_form():
    return render_template('upload.html')


@app.route('/image-to-json-product', methods=['POST'])
def image_to_json_product():
    image_file = request.files['image']
    image = cv2.imdecode(numpy.fromstring(image_file.read(), numpy.uint8), cv2.IMREAD_COLOR)
    extracted_text = pytesseract.image_to_string(image, config='--psm 6 --oem 1', lang='eng')
    rows = extracted_text.split('\n')
    table = [row.split() for row in rows]
    if table and not table[-1]:
        table.pop()
    result = []
    print(table)
    for row in table:
        op = {
            'productName': extractProductFromArray(row),
            'quantity': extractQuantityFromArray(row),
            'unit': extractUnitFromArray(row)
        }
        result.append(op)

    return jsonify({ "result": result, "detected_text": extracted_text})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
