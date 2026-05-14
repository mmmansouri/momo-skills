# Spring Exception Handling

## Table of Contents

1. [RFC 7807 Problem Details (Spring 6+)](#rfc-7807-problem-details-spring-6) — `@RestControllerAdvice`, `ProblemDetail`
2. [Custom Exception Classes](#custom-exception-classes) — base `BusinessException`, specific exceptions

---

## Exception Handling

### RFC 7807 Problem Details (Spring 6+)

```java
@RestControllerAdvice
public class GlobalExceptionHandler extends ResponseEntityExceptionHandler {

    // Resource not found
    @ExceptionHandler(ResourceNotFoundException.class)
    public ProblemDetail handleNotFound(ResourceNotFoundException ex, WebRequest request) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(
            HttpStatus.NOT_FOUND, ex.getMessage());
        problem.setTitle("Resource Not Found");
        problem.setType(URI.create("https://api.example.com/errors/not-found"));
        problem.setInstance(URI.create(getRequestUri(request)));
        return problem;
    }

    // Business rule violation
    @ExceptionHandler(BusinessException.class)
    public ProblemDetail handleBusinessError(BusinessException ex) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(
            HttpStatus.CONFLICT, ex.getMessage());
        problem.setTitle(ex.getTitle());
        problem.setType(URI.create("https://api.example.com/errors/" + ex.getErrorCode()));
        // Custom properties
        problem.setProperty("errorCode", ex.getErrorCode());
        return problem;
    }

    // Validation errors
    @Override
    protected ResponseEntity<Object> handleMethodArgumentNotValid(
            MethodArgumentNotValidException ex,
            HttpHeaders headers,
            HttpStatusCode status,
            WebRequest request) {

        ProblemDetail problem = ProblemDetail.forStatusAndDetail(
            HttpStatus.BAD_REQUEST, "The request contains invalid fields");
        problem.setTitle("Validation Failed");
        problem.setType(URI.create("https://api.example.com/errors/validation-failed"));

        List<Map<String, String>> errors = ex.getBindingResult().getFieldErrors().stream()
            .map(error -> Map.of(
                "field", error.getField(),
                "message", Objects.requireNonNull(error.getDefaultMessage()),
                "rejectedValue", String.valueOf(error.getRejectedValue())))
            .toList();
        problem.setProperty("errors", errors);

        return ResponseEntity.badRequest().body(problem);
    }

    // Constraint violation (path/query params)
    @ExceptionHandler(ConstraintViolationException.class)
    public ProblemDetail handleConstraintViolation(ConstraintViolationException ex) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(
            HttpStatus.BAD_REQUEST, "Invalid request parameters");
        problem.setTitle("Constraint Violation");

        List<Map<String, String>> errors = ex.getConstraintViolations().stream()
            .map(violation -> Map.of(
                "field", violation.getPropertyPath().toString(),
                "message", violation.getMessage()))
            .toList();
        problem.setProperty("errors", errors);

        return problem;
    }

    // Fallback for unexpected errors
    @ExceptionHandler(Exception.class)
    public ProblemDetail handleUnexpected(Exception ex) {
        log.error("Unexpected error", ex);
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(
            HttpStatus.INTERNAL_SERVER_ERROR, "An unexpected error occurred");
        problem.setTitle("Internal Server Error");
        problem.setType(URI.create("https://api.example.com/errors/internal-error"));
        return problem;
    }

    private String getRequestUri(WebRequest request) {
        return ((ServletWebRequest) request).getRequest().getRequestURI();
    }
}
```

### Custom Exception Classes

```java
// Base business exception
public abstract class BusinessException extends RuntimeException {
    private final String errorCode;
    private final String title;

    protected BusinessException(String errorCode, String title, String message) {
        super(message);
        this.errorCode = errorCode;
        this.title = title;
    }

    public String getErrorCode() { return errorCode; }
    public String getTitle() { return title; }
}

// Specific exceptions
public class ResourceNotFoundException extends RuntimeException {
    public ResourceNotFoundException(String resourceType, Object id) {
        super(resourceType + " with ID '" + id + "' was not found");
    }
}

public class DuplicateResourceException extends BusinessException {
    public DuplicateResourceException(String field, String value) {
        super("duplicate-resource",
              "Duplicate Resource",
              "A resource with " + field + " '" + value + "' already exists");
    }
}

public class InsufficientStockException extends BusinessException {
    public InsufficientStockException(String productName, int available, int requested) {
        super("insufficient-stock",
              "Insufficient Stock",
              "Product '" + productName + "' has " + available +
              " units available, but " + requested + " were requested");
    }
}
```
