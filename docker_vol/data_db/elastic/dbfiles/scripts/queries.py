# distinct categories
GET /jobmarket/_search
{
  "size": 0,
  "aggs": {
	"unique_categories": {
	  "terms": {
		"field": "category.keyword"
	  }
	}
  }
}

# all
GET /jobmarket/_search
{
  "query": {
    "match_all": {}
  }
}

# skills not empty
GET /jobmarket/_search
{
  "query": {
    "exists": {
      "field": "skills"
    }
  }
}

# sal_min not empty
GET /jobmarket/_search
{
  "query": {
    "exists": {
      "field": "sal_min"
    }
  }
}

# unique categories
GET /jobmarket/_search
{
  "size": 0,
  "aggs": {
	  "unique_categories": {
	    "terms": {
		    "field": "category.keyword"
	    }
	  } 
  }
}

GET /jobmarket/_mapping
GET /jobmarket/_count
GET /_cluster/health
GET /_cat/shards?v

# increase result listings
PUT /jobmarket/_settings
{
  "settings": {
    "index": {
      "max_result_window": 20000
    }
  }
}

# try
GET /jobmarket/_search
{
  "size": 0,
  "query": {
    "range": {
      "sal_min": {
        "gt": 20000
      }
    }
  },
  "aggs": {
    "unique_categories": {
      "terms": {
        "field": "category.keyword"
      },
      "aggs": {
        "highest_sal_min": {
          "min": {
            "field": "sal_min"
          }
        }
      }
    }
  }
}

# sal variance / category
GET /jobmarket/_search
{
  "size": 0,
  "query": {
    "range": {
      "sal_min": {
        "gt": 20000
      }
    }
  },
  "aggs": {
    "unique_categories": {
      "terms": {
        "field": "category.keyword"
      },
      "aggs": {
        "lowest_sal_min": {
          "min": {
            "field": "sal_min"
          }
        },
        "highest_sal_max":{
          "max": {
            "field": "sal_max"
          }
        }
      }
    }
  }
}

# sal variance / country / category
GET /jobmarket/_search
{
  "size": 0,
  "query": {
    "range": {
      "sal_min": {
        "gt": 20000
      }
    }
  },
  "aggs": {
    "countries": {
      "terms": {
        "field": "location.country"
      },
      "aggs": {
        "unique_categories": {
          "terms": {
            "field": "category.keyword"
          },
          "aggs": {
            "lowest_sal_min": {
              "min": {
                "field": "sal_min"
              }
            },
            "highest_sal_max":{
              "max": {
                "field": "sal_max"
              }
            }
          }
        }
      }
    }
  }
}

# sal variance / category / country
GET /jobmarket/_search
{
  "size": 0,
  "query": {
      "range": {
          "sal_min": {
              "gt": 20000
          }
      }
  },
  "aggs": {
    "unique_categories": {
      "terms": {
        "field": "category.keyword"
      },
      "aggs": {
        "countries": {
          "terms": {
            "field": "location.country"
          },
          "aggs": {
            "lowest_sal_min": {
              "min": {
                "field": "sal_min"
              }
            },
            "highest_sal_max": {
              "max": {
                "field": "sal_max"
              }
            }
          }
        }
      }
    }
  }
}

# no keyword on country despite defined as such
GET /jobmarket/_search
{
  "size": 0,
  "aggs": {
    "find_missing": {
      "missing": {
        "field": "location.country"
      }
    }
  }
}




