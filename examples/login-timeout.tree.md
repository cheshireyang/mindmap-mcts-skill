# Fix intermittent login timeout

- [n1] (V=0.90 N=1 exploring) Fix intermittent login timeout -- Initial goal
  - [n2] (V=0.90 N=1 verified) DB connection pool is exhausted -- Logs contain pool timeout during failed login
  - [n3] (V=0.00 N=0 pruned) Frontend retry storm overloads login -- grep found no retry loop in login client
