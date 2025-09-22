import math


class RegressionAnalysis:
    def __init__(self):
        self.x = [
            0.2,
            0.6,
            0.7,
            1.1,
            1.2,
            1.5,
            1.8,
            2.0,
            2.2,
            2.4,
            2.7,
            3.0,
            3.2,
            3.4,
            3.8,
            4.0,
            4.2,
            4.5,
            4.8,
            5.0,
        ]
        self.y = [
            1.9,
            0.8,
            0.7,
            0.3,
            0.0,
            0.4,
            0.3,
            0.2,
            0.2,
            0.3,
            0.2,
            0.3,
            0.2,
            0.2,
            0.2,
            0.5,
            0.3,
            0.1,
            0.4,
            0.3,
        ]
        self.n = len(self.x)

    def calculate_basic_stats(self):
        """
        Вычисляет базовые статистические характеристики:
        средние значения, суммы, квадраты и произведения.
        """
        self.x_mean = sum(self.x) / self.n
        self.y_mean = sum(self.y) / self.n
        self.sum_x = sum(self.x)
        self.sum_y = sum(self.y)
        self.sum_x2 = sum(xi**2 for xi in self.x)
        self.sum_y2 = sum(yi**2 for yi in self.y)
        self.sum_xy = sum(self.x[i] * self.y[i] for i in range(self.n))

    def correlation_coefficient(self):
        """
        Вычисляет коэффициент корреляции Пирсона.

        Returns:
            float: коэффициент корреляции r.
        """
        num = self.n * self.sum_xy - self.sum_x * self.sum_y
        den = math.sqrt(
            (self.n * self.sum_x2 - self.sum_x**2)
            * (self.n * self.sum_y2 - self.sum_y**2)
        )
        return num / den if den != 0 else 0

    def correlation_significance(self, r):
        """
        Проверяет значимость коэффициента корреляции с помощью t-критерия.

        Args:
            r (float): коэффициент корреляции.

        Returns:
            tuple: (is_significant (bool), t_calc (float)).
        """
        if abs(r) >= 1:
            return True, float("inf")
        t_calc = abs(r) * math.sqrt((self.n - 2) / (1 - r**2))
        t_crit = 2.101  # df=18, alpha=0.05
        return t_calc > t_crit, t_calc

    def linear_regression(self):
        """
        Строит линейную модель: y = a + bx.

        Returns:
            tuple: (a, b) — коэффициенты модели.
        """
        b = (self.n * self.sum_xy - self.sum_x * self.sum_y) / (
            self.n * self.sum_x2 - self.sum_x**2
        )
        a = self.y_mean - b * self.x_mean
        return a, b

    def quadratic_regression(self):
        """
        Строит квадратичную модель: y = a + bx + cx².

        Returns:
            tuple: (a, b, c) — коэффициенты модели.
        """
        Sx = self.sum_x
        Sx2 = self.sum_x2
        Sx3 = sum(x**3 for x in self.x)
        Sx4 = sum(x**4 for x in self.x)
        Sy = self.sum_y
        Sxy = self.sum_xy
        Sx2y = sum((self.x[i] ** 2) * self.y[i] for i in range(self.n))

        D = self.det3([[self.n, Sx, Sx2], [Sx, Sx2, Sx3], [Sx2, Sx3, Sx4]])
        Da = self.det3([[Sy, Sx, Sx2], [Sxy, Sx2, Sx3], [Sx2y, Sx3, Sx4]])
        Db = self.det3([[self.n, Sy, Sx2], [Sx, Sxy, Sx3], [Sx2, Sx2y, Sx4]])
        Dc = self.det3([[self.n, Sx, Sy], [Sx, Sx2, Sxy], [Sx2, Sx3, Sx2y]])

        a = Da / D
        b = Db / D
        c = Dc / D
        return a, b, c

    def cubic_regression(self):
        """
        Строит кубическую модель: y = a + bx + cx² + dx³.

        Returns:
            tuple: (a, b, c, d) — коэффициенты модели.
        """
        Sx = self.sum_x
        Sx2 = self.sum_x2
        Sx3 = sum(x**3 for x in self.x)
        Sx4 = sum(x**4 for x in self.x)
        Sx5 = sum(x**5 for x in self.x)
        Sx6 = sum(x**6 for x in self.x)
        Sy = self.sum_y
        Sxy = self.sum_xy
        Sx2y = sum((self.x[i] ** 2) * self.y[i] for i in range(self.n))
        Sx3y = sum((self.x[i] ** 3) * self.y[i] for i in range(self.n))

        D = self.det4(
            [
                [self.n, Sx, Sx2, Sx3],
                [Sx, Sx2, Sx3, Sx4],
                [Sx2, Sx3, Sx4, Sx5],
                [Sx3, Sx4, Sx5, Sx6],
            ]
        )
        Da = self.det4(
            [
                [Sy, Sx, Sx2, Sx3],
                [Sxy, Sx2, Sx3, Sx4],
                [Sx2y, Sx3, Sx4, Sx5],
                [Sx3y, Sx4, Sx5, Sx6],
            ]
        )
        Db = self.det4(
            [
                [self.n, Sy, Sx2, Sx3],
                [Sx, Sxy, Sx3, Sx4],
                [Sx2, Sx2y, Sx4, Sx5],
                [Sx3, Sx3y, Sx5, Sx6],
            ]
        )
        Dc = self.det4(
            [
                [self.n, Sx, Sy, Sx3],
                [Sx, Sx2, Sxy, Sx4],
                [Sx2, Sx3, Sx2y, Sx5],
                [Sx3, Sx4, Sx3y, Sx6],
            ]
        )
        Dd = self.det4(
            [
                [self.n, Sx, Sx2, Sy],
                [Sx, Sx2, Sx3, Sxy],
                [Sx2, Sx3, Sx4, Sx2y],
                [Sx3, Sx4, Sx5, Sx3y],
            ]
        )

        a = Da / D
        b = Db / D
        c = Dc / D
        d = Dd / D
        return a, b, c, d

    def exponential_regression(self):
        """
        Строит экспоненциальную модель: y = a * exp(bx).

        Returns:
            tuple: (a, b) — коэффициенты модели.
        """
        ln_y = [math.log(yi) for yi in self.y if yi > 0]
        x_valid = [self.x[i] for i in range(self.n) if self.y[i] > 0]
        n = len(x_valid)
        Sx = sum(x_valid)
        Sx2 = sum(x**2 for x in x_valid)
        Sy = sum(ln_y)
        Sxy = sum(x_valid[i] * ln_y[i] for i in range(n))

        b = (n * Sxy - Sx * Sy) / (n * Sx2 - Sx**2)
        ln_a = (Sy - b * Sx) / n
        a = math.exp(ln_a)
        return a, b

    def power_regression(self):
        """
        Строит степенную модель: y = a * x^b.

        Returns:
            tuple: (a, b) — коэффициенты модели.
        """
        ln_x, ln_y = [], []
        for i in range(self.n):
            if self.x[i] > 0 and self.y[i] > 0:
                ln_x.append(math.log(self.x[i]))
                ln_y.append(math.log(self.y[i]))
        n = len(ln_x)
        Sx = sum(ln_x)
        Sx2 = sum(x**2 for x in ln_x)
        Sy = sum(ln_y)
        Sxy = sum(ln_x[i] * ln_y[i] for i in range(n))

        b = (n * Sxy - Sx * Sy) / (n * Sx2 - Sx**2)
        ln_a = (Sy - b * Sx) / n
        a = math.exp(ln_a)
        return a, b

    def calculate_errors(self, y_model):
        """
        Вычисляет ошибки аппроксимации модели.

        Args:
            y_model (list[float]): значения Y, рассчитанные моделью.

        Returns:
            tuple: (rmse, mare, r2, ss_res, ss_tot).
        """
        mse = sum((self.y[i] - y_model[i]) ** 2 for i in range(self.n)) / self.n
        rmse = math.sqrt(mse)
        mare, count = 0, 0
        for i in range(self.n):
            if abs(self.y[i]) > 1e-10:
                mare += abs((self.y[i] - y_model[i]) / self.y[i])
                count += 1
        mare = (mare / count * 100) if count > 0 else 0
        ss_res = sum((self.y[i] - y_model[i]) ** 2 for i in range(self.n))
        ss_tot = sum((self.y[i] - self.y_mean) ** 2 for i in range(self.n))
        r2 = 1 - ss_res / ss_tot if ss_tot != 0 else 0
        return rmse, mare, r2, ss_res, ss_tot

    def model_significance(self, r2, k):
        """
        Проверяет значимость модели с помощью F-критерия Фишера.

        Args:
            r2 (float): коэффициент детерминации.
            k (int): число параметров модели.

        Returns:
            tuple: (is_significant (bool), F (float)).
        """
        df1 = k - 1
        df2 = self.n - k
        if df2 <= 0:
            return False, 0
        F = (r2 / df1) / ((1 - r2) / df2)
        f_crit = 4.41 if df1 == 2 else 3.59
        return F > f_crit, F

    def det3(self, m):
        """
        Вычисляет определитель 3x3.

        Args:
            m (list[list[float]]): матрица 3x3.

        Returns:
            float: значение определителя.
        """
        return (
            m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
            - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
            + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0])
        )

    def det4(self, m):
        """
        Вычисляет определитель 4x4.

        Args:
            m (list[list[float]]): матрица 4x4.

        Returns:
            float: значение определителя.
        """
        det = 0
        for i in range(4):
            minor = [[m[r][c] for c in range(4) if c != i] for r in range(1, 4)]
            det += ((-1) ** i) * m[0][i] * self.det3(minor)
        return det
