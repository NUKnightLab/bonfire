# Bonfire

Automated curation of tweeted content from your Twitterverse


This is a complete re-write of the original Bonfire project from Knight Lab, which is a Tweeted content curator inspired by the Nieman Labs Fuego project.

Design goals for this version of Bonfire include:

 * Architectural simplicity. Reduce the number of architectural dependencies to further enable adoption and deployment.
 * Universe separation. Eliminate the sharing of resources between universes to further simplify the architecture and to facilitate scalability.
 * Leverage Elasticsearch. Since Elastic is being used for content search as a core feature, we will leverage this resource for general storage of Tweets, web content, and resolved URL caching. Consideration for utilizing Elastic as a processing queue is also being considered. In the end, Redis may prove to continue to be the better choice here.
 * Abstract content aggregation and search functions to enable Python-based web applications. Non-Python based applications can connect directly to Elasticsearch.

# Deployment

This is a work in progress. There is currently nothing to deploy. Anticipated deployment will require the following:

 * A running Elasticsearch deployment
 * A seeded universe, expanded with the build-universe script
 * A running Tweet collector (ideally managed by a process manager such as Mozilla Circus, Supervisord, or Upstart)
 * A running Tweet processor (for resolving URLs and extracting web content) -- also managed.
 * A front-end deployment -- presumably a web application that can to Elasticsearch via Bonfire's aggregation & search API

# Development

Bonfire is a set of applications built in Python with the following primary components:

 * universe management script
 * collector script
 * processor script
 * web application

All of these components connect to an Elasticsearch deployment. For development, you should have Elasticsearch running and accessible from your development host. Python dependencies should be installed via pip install -r requirements.txt (ideally in a virtual environment)
