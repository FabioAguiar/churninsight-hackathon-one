package com.churninsight.model.enums;

import com.fasterxml.jackson.annotation.JsonValue;

public enum YesNo {
    YES("Yes"),
    NO("No");  

    private final String value;

    YesNo(String value) {
        this.value = value;
    }

    @JsonValue
    public String getValue() {
        return value;
    }
}
