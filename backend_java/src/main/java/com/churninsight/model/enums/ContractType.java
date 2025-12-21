package com.churninsight.model.enums;

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
}