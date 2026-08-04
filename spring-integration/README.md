# Spring Boot Integration Notes

This folder documents (and, later, may host client code / contracts for)
the Spring Boot side that consumes the Python REST API defined in
`src/api/`.

## Integration contract

- Base URL: configured via `SPRING_BOOT_BASE_URL` / the Python API's own
  host:port (see `.env.example`)
- Auth: TODO — define once security requirements are set (JWT? API key?)
- Content-Type: `application/json`

## Suggested Spring Boot client structure (future work)

```
spring-integration/
└── client/
    ├── XaiAssessmentClient.java   # REST client calling the Python API
    ├── dto/                       # DTOs mirroring src/api/schemas.py
    └── config/                    # RestTemplate / WebClient config
```
