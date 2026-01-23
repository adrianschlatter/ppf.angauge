import pandas as pd
import numpy as np
import matplotlib.pyplot as pl
from matplotlib.widgets import Button, Slider
from matplotlib.gridspec import GridSpec
import ppf.watermeter as wm
from ppf.watermeter.diagnostics import cog
from scipy.optimize import least_squares


class App:
    """
    Interactive app to optimize hand deviations

    Shows hand readings (ones, tens, hundreds, thousands) vs derived maximum
    likelihood estimates. Sliders allow adjustments to hand readings (offset,
    sine distortion, cosine distortion).
    """

    def __init__(self, df, config, dhands=None, ampl_sin=None, ampl_cos=None):
        self.cfgs = wm.read_config(config)
        self.df = df                                # dataframe with readings
        self.hands = df.loc[:, ['E', 'Z', 'H', 'T']].values
        # apply corrections:
        self.hands_corrected = self.correct_hands(
                                        self.hands, dhands, ampl_sin, ampl_cos)
        self.sigmas = df.loc[:, ['dE', 'dZ', 'dH', 'dT']].values
        # calculate max. likelihood estimates from hand readings:
        self.mle = np.array([wm.mle(r)[0] for r
                             in readings_from_array(
                                        self.hands_corrected, self.sigmas)])
        self.handles = {}                             # register plot handles
        self.ax_sliders = {}                          # register axes sliders
        self.wdgt_sliders = {}                        # register slider widgets
        self._create_figure(dhands, ampl_sin, ampl_cos)

    def delta(self, i):
        """Calculate deviation of ML estimate to hand reading for digit i"""
        res = self.mle / 10**i % 10 - self.hands_corrected[:, i]
        res = (res + 5) % 10 - 5

        return res

    @staticmethod
    def correct_hands(hands, dhands=None, ampl_sin=None, ampl_cos=None):
        """Apply hand corrections to given hands"""

        # handle defaults:
        dhands, ampl_sin, ampl_cos = (
            np.zeros((1, 4)) if x is None else np.array(x).reshape((1, 4))
            for x in (dhands, ampl_sin, ampl_cos))
        # apply corrections:
        hands_corrected = hands + dhands
        hands_corrected += (
                    ampl_sin * np.sin(2 * np.pi * hands_corrected / 10)
                    + ampl_cos * np.cos(2 * np.pi * hands_corrected / 10))
        # put hands in [0, 10[:
        hands_corrected = hands_corrected % 10

        return hands_corrected

    def residuals(self, parameters):
        # transform hands according to parameters:
        dhands = parameters[0:4]
        ampl_sin = parameters[4:8]
        ampl_cos = parameters[8:12]
        hands_corrected = self.correct_hands(
                                        self.hands, dhands, ampl_sin, ampl_cos)
        # calculate mle:
        mle = np.array([wm.mle(r)[0]
                        for r in readings_from_array(hands_corrected,
                                                     self.sigmas)])
        # calculate residuals hands(mle) - hands:
        i = np.arange(4)[np.newaxis, :]
        hands_mle = (mle[:, np.newaxis] / 10**i % 10)
        residuals = hands_mle - hands_corrected
        # put residuals in [-5, 5]:
        residuals = (residuals + 5) % 10 - 5
        residuals.shape = (-1,)

        # drop nans:
        residuals = residuals[~np.isnan(residuals)]

        return residuals.reshape(-1)

    def _create_figure(self, dhands, ampl_sin, ampl_cos):
        """Initialize app figure"""

        self.fig = pl.figure(figsize=(15, 6.3))
        self.subfigs = self.fig.subfigures(1, 2, wspace=0.07,
                                           width_ratios=[2, 1.])
        self.axes = self.subfigs[0].subplots(2, 4, sharex=True)
        rmse = np.sqrt(sum([np.nanvar(self.delta(i)) for i in range(4)]) / 4)
        self.subfigs[0].suptitle(
                            f'ML-Estimates vs Hand-Readings - RMSE={rmse:.4f}')
        names = ['Ones', 'Tens', 'Hundreds', 'Thousands']
        for i, col in enumerate('EZHT'):
            ax = self.axes[0][3 - i]
            ax.plot([0, 10], [0, 10], 'k--')
            self.handles[f'MLE_{col}'], = ax.plot(self.hands_corrected[:, i],
                                                  self.mle / 10**i % 10,
                                                  r',', alpha=1)
            if 3 - i == 0:
                ax.set_ylabel('ML Estimate')

            ax = self.axes[1][3 - i]
            delta = self.delta(i)
            self.handles[f'delta_{col}'], = ax.plot(
                    self.hands_corrected[:, i], delta, r',',
                    alpha=1, picker=True)

            ax.set_xlabel(f'{names[i]} Hand')
            ax.set_ylim(-1, +1)
            if 3 - i == 0:
                ax.set_ylabel('Deviation')

        self.subfigs[0].canvas.mpl_connect('pick_event', self.on_pick)

        # Adjust layout; calculate axis width, pitch for later use for sliders:
        self.subfigs[0].subplots_adjust(left=0.08, bottom=0.35, right=0.96,
                                        top=0.9, wspace=0.45)
        axis_w = (0.96 - 0.08) / (4 + 3 * 0.45)
        pitch = axis_w * 1.45

        # Create sliders and buttons:
        self.ax_update = self.subfigs[0].add_axes([0.88, 0.2, 0.08, 0.04])
        self.btn_update = Button(self.ax_update, 'Update')
        self.btn_update.on_clicked(lambda event: self.on_update())

        self.ax_optimize = self.subfigs[0].add_axes([0.04, 0.2, 0.08, 0.04])
        self.btn_optimize = Button(self.ax_optimize, 'Optimize')
        self.btn_optimize.on_clicked(lambda event: self.on_optimize())

        for ax_i, col in enumerate('THZE'):
            ax_slider = self.subfigs[0].add_axes(
                                [0.08 + ax_i * pitch, 0.15, axis_w, 0.04])
            key = f'd{col}'
            val = 0.0 if dhands is None else dhands[3 - ax_i]
            sldr = Slider(ax_slider, key, -1.0, 1.0, valinit=val)
            self.ax_sliders[key] = ax_slider
            self.wdgt_sliders[key] = sldr

            ax_slider = self.subfigs[0].add_axes(
                                [0.08 + ax_i * pitch, 0.1, axis_w, 0.04])
            key = f'{col}sin'
            val = 0.0 if ampl_sin is None else ampl_sin[3 - ax_i]
            sldr = Slider(ax_slider, key, -1.0, 1.0, valinit=val)
            self.ax_sliders[key] = ax_slider
            self.wdgt_sliders[key] = sldr

            ax_slider = self.subfigs[0].add_axes(
                                [0.08 + ax_i * pitch, 0.05, axis_w, 0.04])
            key = f'{col}cos'
            val = 0.0 if ampl_cos is None else ampl_cos[3 - ax_i]
            sldr = Slider(ax_slider, key, -1.0, 1.0, valinit=val)
            self.ax_sliders[key] = ax_slider
            self.wdgt_sliders[key] = sldr

        gs = GridSpec(5, 4, figure=self.subfigs[1])
        # axes for the full image:
        self.ax_img = self.subfigs[1].add_subplot(gs[:2, :])
        # axes for the crops of the clock dials:
        self.ax_color = []
        # axes for the crops converted to hand scale:
        self.ax_handscale = []
        # axes for imgs in polar coordinates:
        self.ax_polar = []
        for i, col in enumerate('EZHT'):
            self.ax_color.append(self.subfigs[1].add_subplot(gs[2, i]))
            self.ax_handscale.append(self.subfigs[1].add_subplot(gs[3, i]))
            self.ax_polar.append(self.subfigs[1].add_subplot(gs[4:, i]))

        self.subfigs[1].subplots_adjust(bottom=0.05, top=0.95)

    def _update_figure(self):
        """Redraw figure with updated data"""
        for i, col in enumerate('EZHT'):
            self.handles[f'MLE_{col}'].set_xdata(self.hands_corrected[:, i])
            self.handles[f'MLE_{col}'].set_ydata(self.mle / 10**i % 10)
            self.handles[f'delta_{col}'].set_xdata(self.hands_corrected[:, i])
            self.handles[f'delta_{col}'].set_ydata(self.delta(i))

        rmse = np.sqrt(sum([np.nanvar(self.delta(i)) for i in range(4)]) / 4)
        self.subfigs[0].suptitle(
                            f'ML-Estimates vs Hand-Readings - RMSE={rmse:.4f}')

        self.subfigs[0].canvas.draw_idle()

    def on_update(self):
        """Update hand corrections and redraw figure"""
        dhand = np.empty((1, 4))
        ampl_sin = np.empty((1, 4))
        ampl_cos = np.empty((1, 4))
        for i, col in enumerate('EZHT'):
            dhand[0, i] = self.wdgt_sliders[f'd{col}'].val
            ampl_sin[0, i] = self.wdgt_sliders[f'{col}sin'].val
            ampl_cos[0, i] = self.wdgt_sliders[f'{col}cos'].val

        self.hands_corrected = self.correct_hands(
                                        self.hands, dhand, ampl_sin, ampl_cos)
        self.mle = np.array(
                    [wm.mle(r)[0]
                     for r in readings_from_array(
                                    self.hands_corrected, self.sigmas)])

        self._update_figure()

    def on_optimize(self):
        """Optimize corrections and update sliders and figure"""
        parameters_init = np.array(
            [self.wdgt_sliders[f'd{col}'].val for col in 'EZHT'] +
            [self.wdgt_sliders[f'{col}sin'].val for col in 'EZHT'] +
            [self.wdgt_sliders[f'{col}cos'].val for col in 'EZHT'])
        result = least_squares(self.residuals, parameters_init, loss='huber')
        parameters_opt = result.x

        for i, col in enumerate('EZHT'):
            self.wdgt_sliders[f'd{col}'].set_val(parameters_opt[i])
            self.wdgt_sliders[f'{col}sin'].set_val(parameters_opt[i + 4])
            self.wdgt_sliders[f'{col}cos'].set_val(parameters_opt[i + 8])

        self.on_update()

    def on_pick(self, event):
        print('onpick line:')
        i = event.ind[0]
        print(self.df.index[i],
              self.hands[i][::-1],
              self.hands_corrected[i][::-1],
              self.mle[i])

        filename = self.df.iloc[event.ind[0]].filename
        img = pl.imread(filename)
        self.ax_img.cla()
        self.ax_img.imshow(img)
        self.ax_img.set_title(f'{filename}')
        for i, col in enumerate('EZHT'):
            cfg = self.cfgs['indicators'][i]
            x0, y0, w = cfg['x0'], cfg['y0'], cfg['w']
            rect = pl.Rectangle((x0, y0), w, w,
                                edgecolor='r', facecolor='none', lw=1.5)
            self.ax_img.add_patch(rect)
            self.ax_color[3 - i].cla()
            crop = img[y0:y0 + w, x0:x0 + w, :]
            self.ax_color[3 - i].imshow(crop)
            self.ax_color[3 - i].set_xticks([])
            self.ax_color[3 - i].set_yticks([])
            gray = wm.to_bw(crop, self.cfgs['fg_mask'], self.cfgs['bg_mask'])
            # for m in range(crop.shape[0]):
            #     for n in range(crop.shape[1]):
            #         gray[m, n] = wm.to_bw(*crop[m, n])
            self.ax_handscale[3 - i].cla()
            self.ax_handscale[3 - i].imshow(gray, cmap='gray', vmin=0, vmax=1)
            self.ax_handscale[3 - i].set_xticks([])
            self.ax_handscale[3 - i].set_yticks([])

            r_min, r_max = 10/40, 1.0  # relative to half image size
            rimg = min(gray.shape) / 2
            n_r, n_theta = 32, 64

            # img_bw = wm.to_bw(gray, self.cfgs['fg_mask'], self.cfgs['bg_mask'])
            img_bw = gray
            img_polar_bw = wm.to_polar(img_bw, n_r, n_theta,
                                       r_min * rimg, r_max * rimg)

            # starting points for flood fill: all points at minimum radius:
            starting_points = set((0, j) for j in range(n_theta))

            # func = wm.ImageFunction(crop, n_r, n_theta,
            #                         r_min * rimg, r_max * rimg,
            #                         threshold=0.5 * gray.max())
            # points = set((0, j) for j in range(n_theta))
            scanned = wm.flood_fill(img_polar_bw, points=starting_points)
            scanned = np.array(list(scanned))
            polar = np.zeros((n_r, n_theta), dtype='float')
            polar[scanned[:, 0], scanned[:, 1]] = 1.0
            x_pixel = np.arange(gray.shape[1]) - gray.shape[1] / 2
            y_pixel = gray.shape[0] / 2 - np.arange(gray.shape[0])
            r2_pixel = x_pixel[None, :]**2 + y_pixel[:, None]**2
            c_x, c_y = cog(gray * (r2_pixel >= r_min**2))
            self.ax_polar[3 - i].cla()
            self.ax_polar[3 - i].imshow(polar, cmap='gray', vmin=0, vmax=1)
            self.ax_handscale[3 - i].plot(
                [0.5 * gray.shape[1]], [0.5 * gray.shape[0]], 'bo', ms=3)
            self.ax_handscale[3 - i].plot(
                [0.5 * gray.shape[1] + c_x], [0.5 * gray.shape[0] - c_y], 'r+')
            self.ax_polar[3 - i].set_xticks([])
            self.ax_polar[3 - i].set_yticks([])
            self.ax_polar[3 - i].set_xlabel(
                                f'{self.hands_corrected[event.ind[0]][i]:.3f}')
            self.ax_polar[3 - i].set_title(
                                f'{self.sigmas[event.ind[0]][i]:.3f}')

        self.subfigs[1].canvas.draw_idle()


def readings_from_array(arr_hands, arr_sigmas):
    """
    Generate readings dictionaries from arrays of hand readings and sigmas
    """
    for row in range(arr_hands.shape[0]):
        readings = []
        for i, col in enumerate(['E', 'Z', 'H', 'T']):
            readings.append({'value': arr_hands[row][i],
                             'sigma': arr_sigmas[row][i]})
        yield readings


if __name__ == '__main__':
    pl.close('all')
    df = pd.read_csv('../experimental/shots_run1/readings.csv',
                     names=['date', 's',
                            'E', 'Z', 'H', 'T',
                            'dE', 'dZ', 'dH', 'dT'],
                     na_values=[' nan'])
    df.loc[:, 'filename'] = '../experimental/shots_run1/' + df.date + '.jpg'
    # we are handling mixed timezone data (DST and non-DST).
    # First, identify which entries are in DST and which are not:
    df.loc[:, 'DST'] = df.date.apply(lambda s: '+02:00' in s)
    # Then, drop the timezone info from date strings:
    df.loc[:, 'date'] = df.date.str[:-6]
    # Make date the index:
    df.set_index('date', inplace=True)
    # Sort the index (sorting is a) important for next step and b) not
    # guaranteed because of chaos happening around DST=>non-DST switch (because
    # of repeated hours):
    df.sort_index(inplace=True)
    # Finally, make the index datetime (instead of string):
    df.index = pd.to_datetime(df.index)

    df = df.loc['2025-10-13':'2025-10-19']
    df.loc[:, 's'] *= 1e4

    app = App(df, '../experimental/shots_run1/config.toml')
