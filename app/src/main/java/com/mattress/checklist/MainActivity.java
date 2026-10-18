package com.mattress.checklist;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.os.Bundle;
import android.print.PrintAttributes;
import android.print.PrintDocumentAdapter;
import android.print.PrintManager;
import android.webkit.JavascriptInterface;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;

/**
 * assets/www 안의 오프라인 체크리스트 웹앱을 보여주는 WebView 컨테이너.
 * 서버 통신 없이 기기 안(클립보드, 인쇄, 로컬 저장소)에서만 데이터를 다룬다.
 */
public class MainActivity extends Activity {

    private WebView webView;

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        webView = findViewById(R.id.webView);
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(true);

        webView.setWebViewClient(new WebViewClient());
        webView.addJavascriptInterface(new WebAppBridge(), "AndroidBridge");
        webView.loadUrl("file:///android_asset/www/index.html");
    }

    @Override
    public void onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }

    /**
     * 웹(JavaScript) 쪽에서 클립보드 복사와 인쇄 기능을 사용하기 위한 브리지.
     * 두 기능 모두 기기 내부에서만 처리되며 외부로 데이터를 전송하지 않는다.
     */
    private class WebAppBridge {

        @JavascriptInterface
        public void copyText(final String text) {
            runOnUiThread(() -> {
                ClipboardManager clipboard =
                        (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
                if (clipboard != null) {
                    ClipData clip = ClipData.newPlainText("mattress_checklist_report", text);
                    clipboard.setPrimaryClip(clip);
                }
                Toast.makeText(MainActivity.this, R.string.copied_toast, Toast.LENGTH_SHORT).show();
            });
        }

        @JavascriptInterface
        public void printPage(final String jobName) {
            runOnUiThread(() -> {
                PrintManager printManager =
                        (PrintManager) getSystemService(Context.PRINT_SERVICE);
                if (printManager == null) {
                    return;
                }
                PrintDocumentAdapter adapter = webView.createPrintDocumentAdapter(jobName);
                printManager.print(jobName, adapter, new PrintAttributes.Builder().build());
            });
        }
    }
}
