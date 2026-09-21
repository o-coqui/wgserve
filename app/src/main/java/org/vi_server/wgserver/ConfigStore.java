package org.vi_server.wgserver;

import android.content.Context;
import android.content.SharedPreferences;

final class ConfigStore {
    private static final String PREFS_NAME = "wgserve_prefs";
    private static final String CONFIG_KEY = "config";

    private ConfigStore() {}

    static SharedPreferences prefs(Context context) {
        return context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
    }

    static String load(Context context) {
        return prefs(context).getString(CONFIG_KEY, null);
    }

    static void save(Context context, String config) {
        prefs(context).edit().putString(CONFIG_KEY, config).apply();
    }
}
