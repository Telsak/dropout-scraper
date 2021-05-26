## Dropout-scraper

**A simple webscraper for dropout.tv (requires subscription login)**
---
This script will traverse https://www.dropout.tv and gather all show data, 
as well as seasons and episodes for each season.

Provide your own login data in the form of a plaintext file (default is 
**dropout.crd**) with the format "Login|Password". If there is no existing file 
you can enter your credentials during runtime as well.

Right now all shows are considered desireable, which will result in some 
overlap. Dropout have shows that are listed on their series page that is 
single seasons of a bigger show. For instance, Dimension 20 have 1 show 
that has 7 seasons, but also other Dimension 20 series that are the same 
as some individual seasons of the main show. Right now you cannot pick and
choose which shows will be scraped.

Upon successful scraping dropout.json will be created which will contain all
shows/season/episodes in the following format:

```python
{ "show": {
  "1": {
    "name": "Show #1", 
    "url": "/show-name-and-url", 
    "season": {
      "1": {
        "name": "Season 1", 
        "url": "https://www.show.url/show/season1", 
        "episode": {
          "1": {
            "url": "https://www.show.url/season1/episode1", 
            "name": "Episode 1 name"
          }, 
          "2": {
            "url": "https://www.show.url/season1/episode2", 
            "name": "Episode 2 name"
          }
        }
      },
      "2": {
        "name": "Season 2", 
        "url": "https://www.dropout.tv/show/season2", 
        "episode": {
          "1": {
            "url": "https://www.show.url/season2/episode1", 
            "name": "Episode 1 name"
          }, 
          "2": {
            "url": "https://www.show.url/season2/episode2", 
            "name": "Episode 2 name"
          }
        }
      }
    }
  }
}
}
```
