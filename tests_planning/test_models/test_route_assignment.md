# Happy Paths
- [x] **Case 1:**
	- Given: `RouteAssignment` with `start_time < end_time`
	- When: `clean` is called
	- Then: `None` should be returned
# Unhappy Paths
- [x] **Case 1:***
	- Given: `RouteAssignment` with `start_time >= end_time`
	- When: `clean` is called
	- Then: a `ValidationError` should be raised with the appropriated message