import { createApp } from "vue";
import App from "./App.vue";
import { store } from "./utils";
import "./global.css";
import duration from 'dayjs/plugin/duration'
import utc from 'dayjs/plugin/utc'
import dayjs from 'dayjs'

dayjs.extend(duration)
dayjs.extend(utc)

createApp(App).use(store).mount("#app");
