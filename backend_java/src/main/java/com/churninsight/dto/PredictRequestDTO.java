package com.churninsight.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
public class PredictRequestDTO {

    @NotNull(message = "O tempo de contrato (tenure) é obrigatório")
    @Min(value = 0, message = "O tempo de contrato não pode ser negativo")
    private Integer tenure;

    @NotBlank(message = "O tipo de contrato é obrigatório")
    private String contract;

    @JsonProperty("internet_service")
    @NotBlank(message = "O serviço de internet é obrigatório")
    private String internetService;

    @JsonProperty("online_security")
    @NotBlank(message = "A segurança online é obrigatória")
    private String onlineSecurity;

    @JsonProperty("tech_support")
    @NotBlank(message = "O suporte técnico é obrigatório")
    private String techSupport;

    @JsonProperty("monthly_charges")
    @NotNull(message = "A cobrança mensal é obrigatória")
    private Double monthlyCharges;

    @JsonProperty("paperless_billing")
    @NotBlank(message = "A opção de conta digital é obrigatória")
    private String paperlessBilling;

    @JsonProperty("payment_method")
    @NotBlank(message = "O método de pagamento é obrigatório")
    private String paymentMethod;
}