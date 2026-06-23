import argparse
import requests

def main():
    parser = argparse.ArgumentParser(description='Upload paper to Shyloneet backend')
    parser.add_argument('--pdf', required=True, help='Path to PDF file')
    parser.add_argument('--api-base', default='http://localhost:8000', help='Base URL of the API')
    parser.add_argument('--exam', default='NEET', help='Exam name')
    parser.add_argument('--year', required=True, type=int, help='Year of the paper')
    parser.add_argument('--set-code', default='Model 10', help='Set code of the paper')
    parser.add_argument('--source', default='Vedantu', help='Source of the paper')
    parser.add_argument('--paper-type', default='questions_with_options_and_answer_key', help='Type of the paper')
    parser.add_argument('--subjects', default='Physics,Chemistry,Biology', help='Subjects of the paper')

    args = parser.parse_args()

    url = args.api_base + '/api/v1/admin/papers/upload_pdf'
    files = {'pdf': open(args.pdf, 'rb')}
    data = {
        'exam': args.exam,
        'year': args.year,
        'set_code': args.set_code,
        'source': args.source,
        'paper_type': args.paper_type,
        'subjects': args.subjects
    }

    response = requests.post(url, files=files, data=data)

    if response.status_code == 200:
        print(response.json())
    else:
        print(f'Error: {response.status_code}')

if __name__ == '__main__':
    main()
