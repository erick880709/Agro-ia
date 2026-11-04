package co.com.bancolombia.api;

import co.com.bancolombia.model.account.Account;

public record AccountView(String id, String number) {
    public static AccountView from(Account account) {
        return new AccountView(account.getId(), account.getNumber());
    }
}
