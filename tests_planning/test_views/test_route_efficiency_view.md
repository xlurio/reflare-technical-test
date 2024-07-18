# Happy Paths
- [x] **Case 1:**
	- Given: `GET` request from an authenticated user specifying an existent `Route`
	- When: request is received
	- Then: a `200` response with the appropriate template rendered in the body and the appropriate `context`
# Unhappy Paths
- [ ] **Case 1:**
	- Given: `GET` request from an unauthenticated user
	- When: request is received
	- Then: a `302` response should be sent redirecting the user to the login page