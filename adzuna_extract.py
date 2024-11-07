import requests

#list of countries to search in
countries=['us','de','fr','ca','gb','ch']
# x sets the number of pages which will be scraped. Page number is a mandatory parameter on Adzuna
x = 10
pages = list(range(1, x + 1))
print(pages)
# job categories to search in
categories = ['engineering-jobs','it-jobs']

with open("results_adzuna.json", "a") as file:
    for country in countries:
         for category in categories:
            for page in pages:
                # add '&sort_by=date' at the end of the URL to order them by date
                # Ideally, the API key must be stored as a SECRET
                URL=f"https://api.adzuna.com/v1/api/jobs/{country}/search/{page}?app_id=f169c798&app_key=147df6984dbd7157b904268ae8b7dee0&category={category}"
                res = requests.get(URL)
                # Check if request was successful
                if res.status_code == 200:
                    # Write response content to file
                    file.write(res.text + "\n")  # Adding newline to separate responses
                else:
                    print(f"Failed to retrieve data for {country}, category {category}, page {page}")