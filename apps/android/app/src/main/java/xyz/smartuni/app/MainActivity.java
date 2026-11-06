package xyz.smartuni.app;

import android.app.Activity;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.HorizontalScrollView;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Primera experiencia nativa SMART UNI. Las secciones no implementadas no
 * muestran datos ficticios ni indican sincronización sin un ACK real.
 */
public final class MainActivity extends Activity {
    private static final int PRIMARY = Color.rgb(43, 128, 236);
    private static final int CTA = Color.rgb(43, 178, 196);
    private static final int TEXT = Color.rgb(36, 52, 72);
    private static final int MUTED = Color.rgb(101, 118, 140);
    private static final int BACKGROUND = Color.rgb(243, 247, 252);
    private final ExecutorService io = Executors.newSingleThreadExecutor();
    private LinearLayout mainContent;
    private String screen = "Inicio";

    @Override public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        showScreen("Inicio");
    }

    private int dp(int size) {
        return (int) (size * getResources().getDisplayMetrics().density + .5f);
    }

    private GradientDrawable rounded(int color) {
        GradientDrawable shape = new GradientDrawable();
        shape.setColor(color);
        shape.setCornerRadius(dp(12));
        return shape;
    }

    private TextView text(String content, int size, int color, boolean bold) {
        TextView widget = new TextView(this);
        widget.setText(content);
        widget.setTextSize(size);
        widget.setTextColor(color);
        if (bold) widget.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        widget.setGravity(Gravity.CENTER_VERTICAL);
        return widget;
    }

    private void addSpacing(LinearLayout container, int height) {
        View spacer = new View(this);
        container.addView(spacer, new LinearLayout.LayoutParams(1, dp(height)));
    }

    private Button button(String title, Runnable action) {
        Button widget = new Button(this);
        widget.setText(title);
        widget.setAllCaps(false);
        widget.setTextColor(Color.WHITE);
        widget.setBackground(rounded(PRIMARY));
        widget.setOnClickListener(view -> action.run());
        return widget;
    }

    private void showScreen(String destination) {
        screen = destination;
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(BACKGROUND);
        root.setFitsSystemWindows(true);

        LinearLayout header = new LinearLayout(this);
        header.setOrientation(LinearLayout.HORIZONTAL);
        header.setGravity(Gravity.CENTER_VERTICAL);
        header.setPadding(dp(20), dp(12), dp(20), dp(12));
        header.setBackgroundColor(Color.WHITE);
        ImageView logo = new ImageView(this);
        logo.setImageResource(R.drawable.smartuni_logo);
        logo.setContentDescription("Isotipo SMART UNI: birrete");
        header.addView(logo, new LinearLayout.LayoutParams(dp(62), dp(58)));
        LinearLayout branding = new LinearLayout(this);
        branding.setOrientation(LinearLayout.VERTICAL);
        branding.addView(text("SMART UNI", 22, PRIMARY, true));
        branding.addView(text("Tu espacio universitario", 13, MUTED, false));
        header.addView(branding);
        root.addView(header);

        HorizontalScrollView navScroll = new HorizontalScrollView(this);
        navScroll.setFillViewport(false);
        navScroll.setHorizontalScrollBarEnabled(false);
        LinearLayout nav = new LinearLayout(this);
        nav.setPadding(dp(10), dp(8), dp(10), dp(8));
        for (String name : new String[] {"Inicio", "Apuntes", "Tareas", "Calendario", "Materiales", "Perfil"}) {
            TextView tab = text(name, 15, name.equals(destination) ? Color.WHITE : TEXT, name.equals(destination));
            tab.setPadding(dp(14), dp(10), dp(14), dp(10));
            tab.setBackground(rounded(name.equals(destination) ? PRIMARY : Color.WHITE));
            tab.setContentDescription("Abrir sección " + name);
            tab.setOnClickListener(v -> showScreen(name));
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(-2, -2);
            lp.setMargins(dp(4), 0, dp(4), 0);
            nav.addView(tab, lp);
        }
        navScroll.addView(nav);
        root.addView(navScroll);

        ScrollView scroller = new ScrollView(this);
        scroller.setFillViewport(true);
        LinearLayout center = new LinearLayout(this);
        center.setGravity(Gravity.TOP | Gravity.CENTER_HORIZONTAL);
        center.setPadding(dp(16), dp(20), dp(16), dp(24));
        mainContent = new LinearLayout(this);
        mainContent.setOrientation(LinearLayout.VERTICAL);
        mainContent.setPadding(dp(20), dp(20), dp(20), dp(20));
        mainContent.setBackground(rounded(Color.WHITE));
        LinearLayout.LayoutParams card = new LinearLayout.LayoutParams(-1, -2);
        card.width = Math.min(getResources().getDisplayMetrics().widthPixels - dp(32), dp(720));
        center.addView(mainContent, card);
        scroller.addView(center);
        root.addView(scroller, new LinearLayout.LayoutParams(-1, 0, 1f));
        setContentView(root);

        mainContent.addView(text(destination, 24, TEXT, true));
        addSpacing(mainContent, 12);
        if ("Apuntes".equals(destination)) {
            showNotes();
        } else if ("Inicio".equals(destination)) {
            showHome();
        } else if ("Perfil".equals(destination)) {
            showProfile();
        } else {
            mainContent.addView(text("Sección preparada para integración con el dominio compartido.", 16, MUTED, false));
            addSpacing(mainContent, 12);
            mainContent.addView(text("Todavía no hay datos sincronizados ni sesión autorizada. No se usarán ejemplos como si fueran datos reales.", 14, MUTED, false));
        }
    }

    private void showHome() {
        mainContent.addView(text("Modo local protegido", 18, CTA, true));
        addSpacing(mainContent, 10);
        mainContent.addView(text("Puedes escribir y abrir un apunte cifrado en este dispositivo. La sincronización y el inicio de sesión aún no están habilitados.", 16, TEXT, false));
        addSpacing(mainContent, 18);
        mainContent.addView(button("Abrir mis apuntes", () -> showScreen("Apuntes")));
        addSpacing(mainContent, 18);
        try {
            int version = NativeBridge.abiVersion();
            boolean valid = NativeBridge.selfTest();
            mainContent.addView(text(valid && version == 1 ? "Núcleo Rust/JNI: autoprueba correcta (ABI 1)" :
                    "Núcleo nativo: verificación fallida", 14, valid ? CTA : Color.RED, false));
        } catch (LinkageError error) {
            mainContent.addView(text("Núcleo nativo no disponible: se impide guardar contenido.", 14, Color.RED, false));
        }
    }

    private void showNotes() {
        mainContent.addView(text("Apunte privado de este dispositivo", 16, TEXT, true));
        addSpacing(mainContent, 8);
        mainContent.addView(text("Solo almacenamiento local cifrado; sin nube ni recuperación todavía.", 14, MUTED, false));
        addSpacing(mainContent, 12);
        EditText editor = new EditText(this);
        editor.setHint("Escribe tu apunte...");
        editor.setTextSize(16);
        editor.setMinLines(5);
        editor.setMaxLines(14);
        editor.setGravity(Gravity.TOP | Gravity.START);
        editor.setInputType(android.text.InputType.TYPE_CLASS_TEXT |
                android.text.InputType.TYPE_TEXT_FLAG_MULTI_LINE |
                android.text.InputType.TYPE_TEXT_FLAG_CAP_SENTENCES);
        editor.setContentDescription("Contenido de apunte privado");
        mainContent.addView(editor, new LinearLayout.LayoutParams(-1, -2));
        TextView status = text("", 14, MUTED, false);
        addSpacing(mainContent, 12);
        try {
            byte[] saved = new EncryptedNotesStore(this).read();
            editor.setText(new String(saved, StandardCharsets.UTF_8));
            Arrays.fill(saved, (byte) 0);
            status.setText("Disponible sin conexión. Los cambios se guardan al pulsar el botón.");
        } catch (Exception | LinkageError error) {
            editor.setEnabled(false);
            status.setText("No se pudo abrir el apunte de forma segura. No se ha sobrescrito.");
            status.setTextColor(Color.RED);
        }
        mainContent.addView(button("Guardar cifrado en dispositivo", () -> {
            byte[] plain = editor.getText().toString().getBytes(StandardCharsets.UTF_8);
            try {
                new EncryptedNotesStore(this).save(plain);
                status.setText("Apunte guardado localmente y cifrado con Rust.");
                status.setTextColor(CTA);
            } catch (Exception | LinkageError failure) {
                status.setText("Error al guardar. Se conserva el contenido anterior.");
                status.setTextColor(Color.RED);
            } finally {
                Arrays.fill(plain, (byte) 0);
            }
        }));
        addSpacing(mainContent, 10);
        mainContent.addView(status);
    }

    private void showProfile() {
        mainContent.addView(text("Sesión: desconectada", 17, MUTED, true));
        addSpacing(mainContent, 8);
        mainContent.addView(text("OIDC/PKCE y enrolamiento seguro de dispositivos son requisitos pendientes. No se aceptan credenciales locales falsas.", 14, TEXT, false));
        addSpacing(mainContent, 18);
        mainContent.addView(text("Diagnóstico HTTPS (solo /healthz; no envía datos privados)", 16, TEXT, true));
        EditText origin = new EditText(this);
        origin.setHint("https://servidor.example");
        origin.setSingleLine(true);
        origin.setInputType(android.text.InputType.TYPE_CLASS_TEXT | android.text.InputType.TYPE_TEXT_VARIATION_URI);
        origin.setContentDescription("Origen HTTPS de diagnóstico");
        mainContent.addView(origin);
        TextView result = text("Sin comprobar", 14, MUTED, false);
        mainContent.addView(button("Comprobar conectividad", () -> {
            String value = origin.getText().toString().trim();
            result.setText("Comprobando mediante JNI...");
            io.execute(() -> {
                int status = NativeBridge.checkHealth(value);
                runOnUiThread(() -> result.setText(status == 200 ? "Servidor HTTPS responde 200" :
                        status > 0 ? "Respuesta HTTP " + status + " (no confirma autenticación)" :
                                "No disponible / URL inválida / fallo de TLS"));
            });
        }));
        addSpacing(mainContent, 12);
        mainContent.addView(result);
    }

    @Override protected void onDestroy() {
        io.shutdownNow();
        super.onDestroy();
    }
}
