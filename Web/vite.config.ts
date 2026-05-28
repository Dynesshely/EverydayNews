import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { NaiveUiResolver } from 'unplugin-vue-components/resolvers'

export default defineConfig({
  base: '/EverydayNews/',
  server: {
    port: 52611,
    strictPort: true,
    proxy: {
      '/proxy/bimg-i0': {
        target: 'https://i0.hdslb.com',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/proxy\/bimg-i0/, ''),
        secure: true,
      },
      '/proxy/bimg-i1': {
        target: 'https://i1.hdslb.com',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/proxy\/bimg-i1/, ''),
        secure: true,
      },
      '/proxy/bimg-i2': {
        target: 'https://i2.hdslb.com',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/proxy\/bimg-i2/, ''),
        secure: true,
      },
    },
  },
  plugins: [
    vue(),
    tailwindcss(),
    AutoImport({
      imports: [
        'vue',
        '@vueuse/core',
        {
          'naive-ui': ['useDialog', 'useMessage', 'useNotification', 'useLoadingBar'],
        },
      ],
      dts: 'src/auto-imports.d.ts',
    }),
    Components({
      resolvers: [NaiveUiResolver()],
      dts: 'src/components.d.ts',
    }),
  ],
})
