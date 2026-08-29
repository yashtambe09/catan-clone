import { configureStore } from '@reduxjs/toolkit'
import authReducer from './authSlice'
import connectionReducer from './connectionSlice'
import roomReducer from './roomSlice'

export const store = configureStore({
  reducer: {
    auth: authReducer,
    connection: connectionReducer,
    room: roomReducer,
  },
})
