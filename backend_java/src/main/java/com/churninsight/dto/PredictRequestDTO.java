package com.churninsight.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

public class PredictRequestDTO {

    @NotNull
    private Integer tenure;

    @NotBlank
    private String contract;

    @JsonProperty("internet_service")
    @NotBlank
    private String internetService;

    @JsonProperty("online_security")
    @NotBlank
    private String onlineSecurity;

    @JsonProperty("tech_support")
    @NotBlank
    private String techSupport;

    @JsonProperty("monthly_charges")
    @NotNull
    private Double monthlyCharger;

    @JsonProperty("paperless_billing")
    @NotBlank
    private String paperless_Billinh;

    @JsonProperty("payment_method")
    @NotBlank
    private String paymentMethod;

    public Integer getTenure() {
        return tenure;
    }

    public void setTenure(Integer tenure) {
        this.tenure = tenure;
    }

    public String getContract() {
        return contract;
    }

    public void setContract(String contract) {
        this.contract = contract;
    }

    public String getInternetService() {
        return internetService;
    }

    public void setInternetService(String internetService) {
        this.internetService = internetService;
    }

    public String getOnlineSecurity() {
        return onlineSecurity;
    }

    public void setOnlineSecurity(String onlineSecurity) {
        this.onlineSecurity = onlineSecurity;
    }

    public String getTechSupport() {
        return techSupport;
    }

    public void setTechSupport(String techSupport) {
        this.techSupport = techSupport;
    }

    public Double getMonthlyCharger() {
        return monthlyCharger;
    }

    public void setMonthlyCharger(Double monthlyCharger) {
        this.monthlyCharger = monthlyCharger;
    }

    public String getPaperless_Billinh() {
        return paperless_Billinh;
    }

    public void setPaperless_Billinh(String paperless_Billinh) {
        this.paperless_Billinh = paperless_Billinh;
    }

    public String getPaymentMethod() {
        return paymentMethod;
    }

    public void setPaymentMethod(String paymentMethod) {
        this.paymentMethod = paymentMethod;
    }

}

