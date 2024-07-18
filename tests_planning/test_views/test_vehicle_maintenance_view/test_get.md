# Happy Paths
- [x] **Case 1:**
	- Given: `GET` request from an authenticated user specifying an existent `Vehicle`
	- When: request is received
	- Then: a `200` response with the header `Content-Type: text/html; charset=utf-8` and the appropriate context
# Unhappy Paths
- [x] **Case 1:**
	- Given: `GET` request from an unauthenticated user
	- When: request is received
	- Then: a `302` response should be sent redirecting the user to the login page
- [ ] **Case 2:**
	- Given: `GET` request from an authenticated user specifying a non existent `Vehicle`
	- When: request is received
	- Then: a `404` error response should be sent