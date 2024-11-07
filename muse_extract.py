import requests

#list of countries to search in
#countries=['us','fr','de','gb']
# x sets the number of pages which will be scraped. Page number is a mandatory parameter on Adzuna
x = 2
pages = list(range(1, x + 1))
print(pages)
# job categories to search in
#categories = ['engineering-jobs','it-jobs']

with open("results_muse.json", "a") as file:
#    for country in countries:
#         for category in categories:
    for page in pages:
        # add '&sort_by=date' at the end of the URL to order them by date
        # Ideally, the API key must be stored as a SECRET
        URL=f"https://www.themuse.com/api/public/jobs?api_key=2c157d8aa46d604b5d390698698525ea8831dd96f1d8e7c1b7d15d19ce6eb608&page={page}"
        res = requests.get(URL)
        # Check if request was successful
        if res.status_code == 200:
            # Write response content to file
            file.write(res.text + "\n")  # Adding newline to separate responses
        else:
            print(f"Failed to retrieve data for page {page}")