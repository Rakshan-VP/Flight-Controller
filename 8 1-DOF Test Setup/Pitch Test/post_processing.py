import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(base_dir, 'sensor_data_09_02_2026.csv')

if not os.path.exists(file_path):
    print(f"Error: {file_path} not found.")
else:
    # Load the data
    df = pd.read_csv(file_path)
    samples = np.arange(len(df))
    time = np.linspace(0, 15.5, len(df))

    # Error Calculations
    comp_error = np.abs(df['pitch_xsens'] - df['pitch_comp'])
    madgwick_error = np.abs(df['pitch_xsens'] - df['pitch_madgwick'])

    plt.style.use('ggplot') 
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 12), sharex=False)
    plt.subplots_adjust(hspace=0.4)

    # --- Plot 1: Pitch Angle Comparison ---
    ax1.plot(samples, df['pitch_xsens'], label='Xsens Pitch (Ref)', color='gray', alpha=0.4, lw=1)
    ax1.plot(samples, df['pitch_comp'], label='Comp Filter ', color='#1f77b4', lw=2)
    ax1.plot(samples, df['pitch_madgwick'], label='Madgwick ', color='#d62728', lw=2)
    
    ax1.set_title('Pitch Axis', fontsize=14)
    ax1.set_ylabel('Angle (degrees)')
    ax1.legend(loc='lower right')
    ax1.grid(True, linestyle='--', alpha=0.7)

    # --- Plot 2: Comp Filter Performance ---
    ax2.fill_between(samples, comp_error, color='#1f77b4', alpha=0.2)
    ax2.plot(samples, comp_error, color='#1f77b4', lw=1.5)
    ax2.set_title('Complementary Filter Absolute Error', fontsize=12)
    ax2.set_ylabel('Error (deg)')
    ax2.grid(True, linestyle=':', alpha=0.6)

    # --- Plot 3: Madgwick Error vs Time ---
    ax3.plot(time, madgwick_error, color='#d62728', lw=1.5)
    ax3.set_title('Madgwick Filter Absolute Error', fontsize=12)
    ax3.set_xlabel('Time (seconds)')
    ax3.set_ylabel('Error (deg)')
    ax3.grid(True, linestyle=':', alpha=0.6)

    # Save and Show
    plot_save_path = os.path.join(base_dir, 'pitch_analysis_plot.png')
    plt.savefig(plot_save_path, dpi=300)
    plt.show()

    print(f"Analysis complete. Plot saved to: {plot_save_path}")