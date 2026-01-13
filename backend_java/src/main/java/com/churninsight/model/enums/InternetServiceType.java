package com.churninsight.model.enums;
import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonValue;

public enum InternetServiceType {
    DSL("DSL"),
    FIBER_OPTIC("Fiber optic"),
    NO("No");

    private final String value;

    InternetServiceType(String value) {
        this.value = value;
    }

    @JsonValue
    public String getValue() {
        return value;
    }

    @JsonCreator
    public static InternetServiceType fromValue(String text) {
        for (InternetServiceType b : InternetServiceType.values()) {
            if (String.valueOf(b.value).equals(text)) {
                return b;
            }
        }
        throw new IllegalArgumentException("Unexpected value'" + text + "'");
    }
}