package com.churninsight.model.enums;
import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonValue;

public enum ContractType {
    MONTH_TO_MONTH("Month-to-month"),
    ONE_YEAR("One year"),
    TWO_YEAR("Two year");

    private final String value;

    ContractType(String value) {
        this.value = value;
    }

    @JsonValue
    public String getValue() {
        return value;
    }

    @JsonCreator
    public static ContractType fromValue(String text) {
        for (ContractType b : ContractType.values()) {
            if (String.valueOf(b.value).equals(text)) {
                return b;
            }
        }
        throw new IllegalArgumentException("Unexpected value '" + text + "'");
    }
}