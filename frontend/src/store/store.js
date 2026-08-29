import { configureStore } from '@reduxjs/toolkit'
import authReducer from './authSlice'
import connectionReducer from './connectionSlice'
import roomReducer from './roomSlice'
import statsReducer from './statsSlice'

export const store = configureStore({
  reducer: {
    auth: authReducer,
    connection: connectionReducer,
    room: roomReducer,
    stats: statsReducer,
  },
})
