import { State } from "@vue/runtime-core";
import { createStore } from "vuex";
import { io } from "socket.io-client";
import _ from "lodash";
import { Axis, Series } from "uplot";
import dayjs from "dayjs";

export const COLORS = [
  "blue",
  "red",
  "green",
  "blueviolet",
  "brown",
  "darkcyan",
  "deepskyblue",
  "indigo",
  "chocolate",
  "crimson",
];

export const getColor = (index: number) => COLORS[index % COLORS.length];

export type PlotPoints = (number | undefined)[];

export enum Status {
  READY = 1,
  CALIBRATING = 2,
  CALIBRATED = 3,
  CALIB_ERR = 4,
  MEASURING = 5,
}

export interface Device {
  id: number;
  name: string;
  serialNumber: string;
}

export interface Marker {
  name: string;
  timestamp: number;
}

export interface Measurement {
  port: string;
  calibFreq: number;
  status: Status;
  device: Device;
  freq: PlotPoints;
  diss: PlotPoints;
  temp: PlotPoints;
  time: PlotPoints;
  freqOffset: PlotPoints;
  dissOffset: PlotPoints;
  tempOffset: PlotPoints;
  timeOffset: PlotPoints;
  offset: {
    freq: number;
  };
  isSelected: boolean;
  isEditOpen: boolean;
  areMarkersShown: boolean;
  data: {
    name: string;
    markers: Marker[];
  };
}

export type DictStr<T> = { [key: string]: T };

export const socket = io("http://localhost:5000/", {
  transports: ["websocket"],
});

export const store = createStore<State>({
  state() {
    return {
      measurements: {},
      isPlotPaused: false,
      firstTime: Number.MAX_SAFE_INTEGER,
    };
  },
  mutations: {
    addMeasurement(state, m: Measurement) {
      m.offset = { freq: 0 };
      m.freqOffset = m.freq;
      m.isSelected = true;
      m.isEditOpen = false;
      m.areMarkersShown = false;
      state.measurements[m.port] = m;

      if (m.time[0] && m.time[0] < state.firstTime) {
        state.firstTime = m.time[0];
      }

      state.firstTime = Number.MAX_SAFE_INTEGER;
      _.values(state.measurements).forEach((m) => {
        if (m.time[0] && m.time[0] < state.firstTime) {
          state.firstTime = m.time[0];
        }
      });

      state.isPlotPaused = false;
    },
    setIsPlotPaused(state, isPlotPaused) {
      state.isPlotPaused = isPlotPaused;
    },
    addMarker(state, { port, marker }: { port: string; marker: Marker }) {
      state.measurements[port].data.markers.push(marker);
    },
    removeMarker(state, { port, index }: { port: string; index: number }) {
      state.measurements[port].data.markers.splice(index, 1);
    },
    setOffset(state, time) {
      _.values(state.measurements).forEach((m) => {
        m.offset.freq = m.freq[time] || 0;
        m.freqOffset = m.freq.map((f) =>
          f === undefined ? f : f - m.offset.freq
        );
      });
      state.isPlotPaused = false;
    },
    data(state, data: Array<[string, number, number, number, number]>) {
      data.forEach(([port, ...values]) => {
        const m = state.measurements[port];
        const [freq, diss, temp, time] = values;

        if (!m) {
          return;
        }

        if (
          (!m.time.length || (m.time as number[])[0] > state.firstTime) &&
          state.firstTime < Number.MAX_SAFE_INTEGER
        ) {
          const diff = ((m.time as number[])[0] || time) - state.firstTime;
          m.freq = [...Array(diff), ...m.freq];
          m.freqOffset = [...Array(diff), ...m.freqOffset];
          m.diss = [...Array(diff), ...m.diss];
          m.temp = [...Array(diff), ...m.temp];
          m.time = [...Array(diff), ...m.time];

          // console.log("freq", m.freqOffset);
        }

        m.calibFreq = freq;
        m.freqOffset.push(freq - m.offset.freq);
        m.freq.push(freq);
        m.diss.push(diss);
        m.temp.push(temp);
        m.time.push(time);

        if (time < state.firstTime) {
          state.firstTime = time;
        }
      });
    },
  },
  getters: {
    plotData(state) {
      let data: { freq: [PlotPoints, ...PlotPoints] } = { freq: [[]] };
      const measurements = _.values(state.measurements);

      measurements.forEach((m) => {
        data.freq.push(m.freqOffset);
      });

      if (measurements.length > 0 && measurements[0].time.length >= 2) {
        data.freq[0] = measurements[0].time;
      }

      return data;
    },
    plotSeries(state): Series[] {
      return _.values(state.measurements).map((m, i) => ({
        label: m.port,
        stroke: getColor(i),
      }));
    },
    plotTimeSeries(state): Series {
      return {
        label: "Time",
        value: (self, value) => {
          const diff = value - state.firstTime;
          const timeDiff = dayjs.utc(diff * 1000).format("HH:mm:ss");
          const time = dayjs(value * 1000).format("HH:mm:ss");
          return `${time} (+${timeDiff}, offset: ${diff})`;
        },
      };
    },
    plotTimeAxis(state): Axis {
      return {
        label: "Time",
        values: (self, values) =>
          values.map((value) =>
            dayjs.utc((value - state.firstTime) * 1000).format("HH:mm:ss")
          ),
      };
    },
    selectedPorts(state): string[] {
      return _.values(state.measurements)
        .filter((m) => m.isSelected)
        .map((m) => m.port);
    },
    selectedMeasurements(state): Measurement[] {
      return _.values(state.measurements).filter((m) => m.isSelected);
    },
  },
});

socket.onAny((event, data) => {
  console.log(event, data);
});

socket.on("data", (data) => {
  store.commit("data", data);
});

socket.on("addMeasurement", (measurement: Measurement) => {
  store.commit("addMeasurement", measurement);
});
